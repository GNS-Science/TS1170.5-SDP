"""
This module derives the PGA, Sa,s, Tc, and Td parameters from the NSHM hazard curves.
"""
import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from nzssdt_2023.data_creation.constants import (
    IMT_LIST,
    LOCATION_REPLACEMENTS,
    LOWER_BOUND_PARAMETERS,
    PGA_N_DP,
    PGA_REDUCTIONS,
    PSV_N_DP,
    SAS_N_DP,
    SITE_CLASSES,
    TC_N_SF,
    VS30_LIST,
    LocationReplacement,
)
from nzssdt_2023.data_creation.extract_data import (
    extract_APoEs,
    extract_quantiles,
    extract_sites,
    extract_spectra,
)
from nzssdt_2023.data_creation.NSHM_to_hdf5 import acc_to_vel, g, period_from_imt

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    import numpy.typing as npt
    import pandas.typing as pdt

PGA_REDUCTION_ENABLED = (
    True  # for testing only, False skips `reduce_PGAs()` function call.
)
PGA_ROUNDING_ENABLED = True  # for testing only, as above.


def choose_site_class(vs30: Union[int, float], lower_bound: bool = False) -> str:
    """Returns the site class for the selected vs30 value
    Site class definitions can be found in TS Table 3.1

    Note that the site class returned here is based on vs30 alone, i.e. the a) clauses in Table 3.1

    Args:
        vs30: vs30 of interest [m/s]
        lower_bound: False returns the site class as defined in TS Table 3.1
                     True returns the alternate site class at the vs30 discontinuity

    Returns:
        sc: site class
    """

    min_vs30 = SITE_CLASSES["VI"].lower_bound

    if vs30 > min_vs30:
        boundaries = np.array([SITE_CLASSES[sc].lower_bound for sc in SITE_CLASSES])

        # switches which SC is selected at the boundary
        if lower_bound:
            side = "left"
        else:
            side = "right"

        sc_idx = np.searchsorted(-boundaries, -vs30, side=side)  # type: ignore
        sc = [SITE_CLASSES[sc].site_class for sc in SITE_CLASSES][sc_idx]

    elif (vs30 == min_vs30) & lower_bound:
        sc = "VI"

    else:
        sc = "VII"

    return sc


def sig_figs(
    x: Union[float, List[float], "npt.NDArray"], n: int
) -> Union[float, "npt.NDArray"]:
    """Rounds all values of x to n significant figures

    Inputs:
        x: float value(s)
        n: number of significant digits

    Returns:
        x_rounded: x rounded to n digits
    """
    x = np.asarray(x)
    x_positive = np.where(np.isfinite(x) & (x != 0), np.abs(x), 10 ** (n - 1))
    mags = 10 ** (n - 1 - np.floor(np.log10(x_positive)))
    x_rounded = np.round(x * mags) / mags
    return x_rounded


def acc_spectra_to_vel(acc_spectra: "npt.NDArray", imtls: dict) -> "npt.NDArray":
    """Convert uniform hazard spectra from acceleration to velocity

    Args:
        acc_spectra: acceleration spectra
        imtls: keys: intensity measures e.g., SA(1.0), values: list of intensity levels

    Returns:
        vel_spectra: velocity spectra

    """
    vel_spectra = np.zeros_like(acc_spectra)
    period_list = [period_from_imt(imt) for imt in list(imtls.keys())]

    for i_p, period in enumerate(period_list):
        vel_spectra[:, :, i_p, :, :] = acc_to_vel(acc_spectra[:, :, i_p, :, :], period)

    return vel_spectra


def calc_R_PGA(pga: float, site_class: str) -> float:
    """Calculate the reduction factor for the peak ground acceleration (Eq. C3.15)

    Args:
        pga: peak ground acceleration [g]
        site_class: roman numeral

    Returns:
        r_pga: reduction factor for peak ground acceleration

    """
    r_pga = 0

    if site_class in PGA_REDUCTIONS.keys():
        A0 = PGA_REDUCTIONS[site_class].A0
        A1 = PGA_REDUCTIONS[site_class].A1
        PGA_threshold = PGA_REDUCTIONS[site_class].PGA_threshold

        if pga >= PGA_threshold:
            r_pga = A0 * np.log(pga) + A1

    return r_pga


def calc_reduced_PGA(pga: float, site_class: str) -> float:
    """Calculate the adjusted peak ground acceleration (Eq. C3.14)

    Args:
        pga: peak ground acceleration [g]
        site_class: roman numeral

    Returns:
        reduced_pga: adjusted peak ground acceleration
    """
    r_pga = calc_R_PGA(pga, site_class)
    reduced_pga = pga * (1 - r_pga)

    return reduced_pga


def reduce_PGAs(PGA: "npt.NDArray") -> "npt.NDArray":
    """Apply peak ground acceleration adjustments to all PGA values (Eq. C3.14)

    Args:
        PGA: peak ground acceleration

    Returns:
        reduced_PGA: adjusted peak ground acceleration
    """
    n_vs30s, n_sites, n_rps, n_stats = PGA.shape
    reduced_PGA = PGA.copy()

    for sc in PGA_REDUCTIONS.keys():
        vs30 = int(SITE_CLASSES[sc].representative_vs30)
        i_vs30 = VS30_LIST.index(vs30)
        for i_site in range(n_sites):
            for i_rp in range(n_rps):
                for i_stat in range(n_stats):
                    pga = PGA[i_vs30, i_site, i_rp, i_stat]
                    reduced_PGA[i_vs30, i_site, i_rp, i_stat] = calc_reduced_PGA(
                        pga, sc
                    )

    return reduced_PGA


def uhs_value(
    period: Union[float, "npt.NDArray"], PGA: float, Sas: float, Tc: float, Td: float
) -> float:
    """Derive the spectral acceleration Sa(T) at a given period (T), based on the seismic demand parameters.
    Sa(T) equations come from TS Eq. 3.2-3.5

    Args:
        period: period, T, a which the spectral acceleration is calculated [seconds]
        PGA: peak ground acceleration [g]
        Sas: short-period spectral acceleration [g]
        Tc: spectral-acceleration-plateau corner period [seconds]
        Td: spectral-velocity-plateau corner period [seconds]

    Todo:
        this works (i.e. it handles the code as it's called now) -  but
        I think there's a better way to do this sort of thing whe your data is in numpy arrays
        see: https://stackoverflow.com/questions/42594695/
        how-to-apply-a-function-map-values-of-each-element-in-a-2d-numpy-array-matrix

    Returns:
        SaT: spectral acceleration [g]
    """
    if isinstance(period, np.ndarray):
        assert len(period) == 1
        period = float(period[0])

    if period == 0:
        SaT = PGA
    elif period < 0.1:
        SaT = PGA + (Sas - PGA) * (period / 0.1)
    elif period < Tc:
        SaT = Sas
    elif period < Td:
        SaT = Sas * Tc / period
    else:
        SaT = Sas * Tc / period * (Td / period) ** 0.5

    return float(SaT)


def interpolate_spectra(
    spectra: "npt.NDArray", imtls: dict, dt: float = 0.1
) -> Tuple["npt.NDArray", "npt.NDArray"]:
    """Linearly interpolate spectra over the original domain, in increments of dt

    Inputs:
        spectra: acceleration spectra
        imtls: keys: intensity measures e.g., SA(1.0), values: list of intensity levels
        dt: period increments at which to interpolate

    Returns:
        new_spectra: interpolated spectra
        new_period_list: periods at which the spectra are defined
    """
    n_vs30s, n_sites, n_periods, n_apoes, n_stats = spectra.shape

    period_list = np.array([period_from_imt(imt) for imt in imtls.keys()])
    new_period_list = np.arange(min(period_list), max(period_list) + dt, dt)

    new_spectra = np.zeros([n_vs30s, n_sites, len(new_period_list), n_apoes, n_stats])
    for i_vs30 in range(n_vs30s):
        for i_site in range(n_sites):
            for i_apoe in range(n_apoes):
                for i_stat in range(n_stats):
                    new_spectra[i_vs30, i_site, :, i_apoe, i_stat] = np.interp(
                        new_period_list,
                        period_list,
                        spectra[i_vs30, i_site, :, i_apoe, i_stat],
                    )

    return new_spectra, new_period_list


def relevant_spectrum_domain(
    spectrum: "npt.NDArray", periods: "npt.NDArray", tc: float, inclusive: bool = False
) -> Tuple["npt.NDArray", "npt.NDArray"]:
    """Return the spectrum over the relevant domain for potential values of Td

    Args:
        spectrum: acceleration spectrum [g]
        periods:  periods as which spectrum is defined [seconds]
        tc:       spectral-acceleration-plateau corner period [seconds]
        inclusive: if true, the range includes the tc+0.5 value
                   (e.g. for Tc+0.5 = 0.75, 0.7 <= Td rather than 0.8 <= Td)

    Returns:
        relevant_spectrum: spectrum over the relevant periods
        relevant_periods: periods included in the relevant domain
    """
    max_T = 6
    max_idx = np.searchsorted(periods, max_T, side="right")

    min_T = tc + 0.5
    min_idx = np.searchsorted(periods, min_T)
    if (sig_figs(periods[min_idx], 2) > min_T) & inclusive:
        periods[min_idx]
        min_idx -= 1

    relevant_periods = periods[min_idx:max_idx]
    relevant_spectrum = spectrum[min_idx:max_idx]

    return relevant_spectrum, relevant_periods


def Td_fit_error(
    td: float,
    relevant_periods: "npt.NDArray",
    relevant_spectrum: "npt.NDArray",
    pga=float,
    sas=float,
    tc=float,
) -> float:
    """Calculate the spectral fit error term for the selected td value.
    The error is evaluated as the sum of the square root of the absolute difference between
    the fit spectrum and the original spectrum, at relevant periods.

    Args:
        td: spectral-velocity-plateau corner period [seconds]
        relevant_periods: periods included in the relevant domain [seconds]
        relevant_spectrum: spectrum over the relevant periods [g]
        pga: peak ground acceleration [g]
        sas: short-period spectral acceleration [g]
        tc: spectral-acceleration-plateau corner period [seconds]

    Returns:
        error: error term
    """
    fitted_spectrum = np.array(
        [uhs_value(period, pga, sas, tc, td) for period in relevant_periods]
    )
    error_array = np.abs(relevant_spectrum - fitted_spectrum)
    error = np.sum(error_array**2)
    return error


def fit_Td(
    spectrum: "npt.NDArray", periods: "npt.NDArray", pga: float, sas: float, tc: float
) -> float:
    """Fit the Td value to obtain the best fit over the response spectrum

    Args:
        spectrum: acceleration spectrum [g]
        periods:  periods over which spectrum is defined [seconds]
        pga: peak ground acceleration [g]
        sas: short-period spectral acceleration [g]
        tc: spectral-acceleration-plateau corner period [seconds]

    Returns:
        td: spectral-velocity-plateau corner period [seconds]
    """
    relevant_spectrum, relevant_periods = relevant_spectrum_domain(
        spectrum, periods, tc
    )

    # select period with the minimum error
    td_error = [
        Td_fit_error(td, relevant_periods, relevant_spectrum, pga, sas, tc)
        for td in relevant_periods
    ]
    td = relevant_periods[np.argmin(td_error)]

    return td


def fit_Td_array(
    PGA: "npt.NDArray",
    Sas: "npt.NDArray",
    Tc: "npt.NDArray",
    acc_spectra: "npt.NDArray",
    imtls: dict,
    site_list: List[str],
    vs30_list: List[int],
    hazard_rp_list: List[int],
    i_stat: int = 0,
    sites_of_interest: Optional[List[str]] = None,
) -> "npt.NDArray":
    """Fit the Td values for all sites, site classes and APoE of interest

    Args:
        PGA: adjusted peak ground acceleration [g] (Eqn C3.14)
        Sas: short-period spectral acceleration [g] (90% of maximum spectral acceleration)
        Tc : spectral-acceleration-plateau corner period [seconds]
        acc_spectra: acceleration spectra [g]
        imtls: keys: intensity measures e.g., SA(1.0), values: list of intensity levels
        site_list: sites included in acc_spectra
        vs30_list: vs30s included in acc_spectra
        hazard_rp_list: return periods included in acc_spectra
        i_stat: spectra index for stats in ['mean'] + quantiles
        sites_of_interest: subset of sites

    Returns:
        Td: spectral-velocity-plateau corner period [seconds]
    """
    if sites_of_interest is None:
        sites_of_interest = site_list

    interpolated_spectra, periods = interpolate_spectra(acc_spectra, imtls)
    n_vs30s, _, n_periods, n_apoes, n_stats = interpolated_spectra.shape
    n_sites = len(sites_of_interest)
    Td = np.zeros([n_vs30s, n_sites, n_apoes])
    # print(type(Td))

    # cycle through all hazard parameters
    count = 0
    expected_count = n_sites
    for i_site_int, site in enumerate(sites_of_interest):
        count += 1
        log.info(
            f"fit_Td_array progress: Site #{count} of {expected_count}. "
            f"Approx {(count / expected_count) * 100:.1f} % progress. "
        )

        for vs30 in vs30_list:
            for rp in hazard_rp_list:
                i_site = site_list.index(site)
                i_vs30 = vs30_list.index(vs30)
                i_rp = hazard_rp_list.index(rp)

                spectrum = interpolated_spectra[i_vs30, i_site, :, i_rp, i_stat]

                pga = PGA[i_vs30, i_site, i_rp, i_stat]
                sas = Sas[i_vs30, i_site, i_rp, i_stat]
                tc = Tc[i_vs30, i_site, i_rp, i_stat]

                Td[i_vs30, i_site_int, i_rp] = fit_Td(spectrum, periods, pga, sas, tc)

    return Td


def calculate_parameter_arrays(
    data_file: str | Path,
) -> Tuple["npt.NDArray", "npt.NDArray", "npt.NDArray", "npt.NDArray"]:
    """Calculate PGA, Sa,s, and Tc values for uniform hazard spectra in hdf5

    Args:
        data_file: name of hazard hdf5 file

    Returns:
        PGA: adjusted peak ground acceleration [g] (Eqn C3.14)
        Sas: short-period spectral acceleration [g] (90% of maximum spectral acceleration)
        PSV: 95% of maximum spectral velocity [m/s]
        Tc : spectral-acceleration-plateau corner period [seconds]
    """

    acc_spectra, imtls = extract_spectra(data_file)
    vel_spectra = acc_spectra_to_vel(acc_spectra, imtls)

    PGA = acc_spectra[:, :, IMT_LIST.index("PGA"), :, :]

    if PGA_REDUCTION_ENABLED:
        log.debug(f"PGA array {PGA}")
        PGA = reduce_PGAs(PGA)
    else:
        log.warning(
            f"PGA reduction skipped because `PGA_REDUCTION_ENABLED` == {PGA_REDUCTION_ENABLED}"
        )

    if PGA_ROUNDING_ENABLED:
        PGA = np.round(PGA, PGA_N_DP)
    else:
        log.warning(
            f"PGA rounding skipped because `PGA_ROUNDING_ENABLED` == {PGA_ROUNDING_ENABLED}"
        )

    Sas = 0.9 * np.max(acc_spectra, axis=2)
    Sas = np.round(Sas, SAS_N_DP)

    PSV = 0.95 * np.max(vel_spectra, axis=2)
    Tc = 2 * np.pi * PSV / (Sas * g)
    Tc = sig_figs(Tc, TC_N_SF)

    return PGA, Sas, PSV, Tc


def create_mean_sa_table(
    PGA, Sas, PSV, Tc, mean_Td, site_list, vs30_list, hazard_rp_list
):
    i_stat = 0  # spectra index for stats in ['mean'] + quantiles

    index = site_list
    APoEs = [f"APoE: 1/{rp}" for rp in hazard_rp_list]
    site_class_list = [f"{SITE_CLASSES[sc].label}" for sc in SITE_CLASSES]
    parameters = ["PGA", "Sas", "PSV", "Tc", "Td"]
    columns = pd.MultiIndex.from_product([APoEs, site_class_list, parameters])
    df = pd.DataFrame(index=index, columns=columns).astype(float)

    log.info("create_mean_sa_table() processesing site classes")
    for sc in SITE_CLASSES.keys():
        sc_label = SITE_CLASSES[sc].label
        vs30 = int(SITE_CLASSES[sc].representative_vs30)
        i_vs30 = vs30_list.index(vs30)

        log.info(f"site class {sc} label: {sc_label} vs30: {vs30}")

        for APoE, rp in zip(APoEs, hazard_rp_list):
            i_rp = hazard_rp_list.index(rp)

            df.loc[:, (APoE, sc_label, "PGA")] = PGA[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "Sas")] = Sas[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "PSV")] = PSV[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "Tc")] = Tc[i_vs30, :, i_rp, i_stat]
            df.loc[:, (APoE, sc_label, "Td")] = mean_Td[i_vs30, :, i_rp]

    return df


def update_lower_bound_sa(
    mean_df,
    PGA,
    Sas,
    Tc,
    PSV,
    acc_spectra,
    imtls,
    vs30_list,
    hazard_rp_list,
    quantile_list,
):
    site_list = list(mean_df.index)
    index = site_list

    APoEs = [f"APoE: 1/{rp}" for rp in hazard_rp_list]
    site_class_list = [f"{SITE_CLASSES[sc].label}" for sc in SITE_CLASSES]
    parameters = ["PGA Floor", "Sas Floor", "PSV Floor", "Td Floor", "PSV adjustment"]
    columns = pd.MultiIndex.from_product([APoEs, site_class_list, parameters])
    df = pd.concat([mean_df, pd.DataFrame(index=index, columns=columns)], axis=1)

    controlling_site = LOWER_BOUND_PARAMETERS["controlling_site"]
    i_site = site_list.index(controlling_site)
    i_stat = 1 + quantile_list.index(
        float(LOWER_BOUND_PARAMETERS["controlling_percentile"])
    )
    log.debug(
        f"update_lower_bound_sa() controlling_site: {controlling_site};"
        f' controlling_percentile {LOWER_BOUND_PARAMETERS["controlling_percentile"]}'
    )
    lower_bound_Td = fit_Td_array(
        PGA,
        Sas,
        Tc,
        acc_spectra,
        imtls,
        site_list,
        vs30_list,
        hazard_rp_list,
        i_stat,
        [controlling_site],
    )

    log.info("update_lower_bound_sa() processesing site classes")
    for sc in SITE_CLASSES.keys():
        sc_label = SITE_CLASSES[sc].label
        vs30 = int(SITE_CLASSES[sc].representative_vs30)
        i_vs30 = vs30_list.index(vs30)

        log.info(f"site class {sc} label: {sc_label} vs30: {vs30}")

        for APoE, rp in zip(APoEs, hazard_rp_list):
            i_rp = hazard_rp_list.index(rp)

            # update the controlling site to use the qth %ile
            df.loc[controlling_site, (APoE, sc_label, "PGA")] = PGA[
                i_vs30, i_site, i_rp, i_stat
            ]
            df.loc[controlling_site, (APoE, sc_label, "Sas")] = Sas[
                i_vs30, i_site, i_rp, i_stat
            ]
            df.loc[controlling_site, (APoE, sc_label, "PSV")] = PSV[
                i_vs30, i_site, i_rp, i_stat
            ]
            df.loc[controlling_site, (APoE, sc_label, "Tc")] = Tc[
                i_vs30, i_site, i_rp, i_stat
            ]
            df.loc[controlling_site, (APoE, sc_label, "Td")] = lower_bound_Td[
                i_vs30, 0, i_rp
            ]

            # apply lower bound to all sites for PGA, Sas, and PSV
            df.loc[:, (APoE, sc_label, "PGA")] = np.maximum(
                df.loc[:, (APoE, sc_label, "PGA")],
                df.loc[controlling_site, (APoE, sc_label, "PGA")],
            )
            df.loc[:, (APoE, sc_label, "Sas")] = np.maximum(
                df.loc[:, (APoE, sc_label, "Sas")],
                df.loc[controlling_site, (APoE, sc_label, "Sas")],
            )
            df.loc[:, (APoE, sc_label, "PSV")] = np.maximum(
                df.loc[:, (APoE, sc_label, "PSV")],
                df.loc[controlling_site, (APoE, sc_label, "PSV")],
            )

            # record locations that were controlled by the lower bound
            df.loc[:, (APoE, sc_label, "PGA Floor")] = ~(
                df.loc[:, (APoE, sc_label, "PGA")]
                > df.loc[controlling_site, (APoE, sc_label, "PGA")]
            )
            df.loc[:, (APoE, sc_label, "Sas Floor")] = ~(
                df.loc[:, (APoE, sc_label, "Sas")]
                > df.loc[controlling_site, (APoE, sc_label, "Sas")]
            )
            df.loc[:, (APoE, sc_label, "PSV Floor")] = ~(
                df.loc[:, (APoE, sc_label, "PSV")]
                > df.loc[controlling_site, (APoE, sc_label, "PSV")]
            )

            # set new Tc values
            tc = (
                2
                * np.pi
                * df.loc[:, (APoE, sc_label, "PSV")]
                / (df.loc[:, (APoE, sc_label, "Sas")] * g)
            )
            df.loc[:, (APoE, sc_label, "Tc")] = sig_figs(tc, TC_N_SF)

            # infer new rounded PSV values from rounded Tcs
            psv = (
                df.loc[:, (APoE, sc_label, "Tc")]
                * df.loc[:, (APoE, sc_label, "Sas")]
                * g
            ) / (2 * np.pi)
            df.loc[:, (APoE, sc_label, "PSV")] = np.round(psv, PSV_N_DP)
            # psv_original = df.loc[:, (APoE, sc_label, "PSV")]
            # df.loc[:, (APoE, sc_label, "PSV adjustment")] = (
            #     df.loc[:, (APoE, sc_label, "PSV")] - psv_original
            # )
            # log.info(f"site class {sc}, APoE: {APoE}, max PSV adjustment:
            #    {df.loc[:, (APoE, sc_label, 'PSV adjustment')]}")
            # log.info(df.loc[:, (APoE, sc_label, slice(None))])

            # set new Td if PSV is controlled by the lower bound
            df.loc[:, (APoE, sc_label, "Td Floor")] = False
            for site in site_list:
                if df.loc[site, (APoE, sc_label, "PSV Floor")]:
                    if (
                        df.loc[controlling_site, (APoE, sc_label, "Td")]
                        >= df.loc[site, (APoE, sc_label, "Td")]
                    ):
                        df.loc[site, (APoE, sc_label, "Td")] = df.loc[
                            controlling_site, (APoE, sc_label, "Td")
                        ]
                        df.loc[site, (APoE, sc_label, "Td Floor")] = True

    return df


def remove_irrelevant_location_replacements(
    site_list: List[str], location_replacements: dict[str, LocationReplacement]
) -> dict[str, LocationReplacement]:
    """

    Args:
        site_list: list of sites included in the sa tables
        location_replacements: list of the location replacements

    Returns:
        location_replacements: a new dictionary of replacements

    """
    new_location_replacements = {}

    for key in location_replacements.keys():
        if key in site_list:
            replace_list = location_replacements[key].replaced_locations
            new_location_replacements[key] = LocationReplacement(
                key, [site for site in replace_list if site in site_list]
            )

    return new_location_replacements


def replace_relevant_locations(
    df: "pdt.DataFrame", print_locations: bool = False
) -> "pdt.DataFrame":
    """replace parameters for locations that are tied to other locations

    Args:
        df: mutli-index dataframe including all sites, annual probabilities of exceedance, and site classes
        print_locations: if True, print relevant locations before and after replacements

    Returns:
        df: mutli-index dataframe with replaced locations

    """
    site_list = list(df.index)
    location_replacements = remove_irrelevant_location_replacements(
        site_list, LOCATION_REPLACEMENTS
    )

    if print_locations:
        check_replaced_locations = []
        for location in location_replacements:
            check_replaced_locations.append(location)
            for replaced_location in location_replacements[location].replaced_locations:
                check_replaced_locations.append(replaced_location)
        print("\n\noriginal values for replaced locations:")
        print(df.loc[check_replaced_locations, :])

    for location in location_replacements:
        for replaced_location in location_replacements[location].replaced_locations:
            df.loc[replaced_location, :] = df.loc[location, :]

    if print_locations:
        print("\n\nnew values for replaced locations:")
        print(df.loc[check_replaced_locations, :])

    return df


def remove_lower_bound_metadata(df: "pdt.DataFrame"):
    """Removes the metadata flags related to the lower bound hazard

    Args:
        df: mutli-index dataframe of sa parameters for all locations, APoEs, and site classes

    Returns:
        df: same df with fewer columns
    """

    df = df.copy(deep=True)

    APoEs = list(df.columns.levels[0])
    sc_labels = list(df.columns.levels[1])

    for APoE in APoEs:
        for sc in sc_labels:
            for parameter in [
                "PGA Floor",
                "PSV",
                "PSV Floor",
                "Sas Floor",
                "Td Floor",
                "PSV adjustment",
            ]:
                df.drop((APoE, sc, parameter), axis=1, inplace=True)

    return df


def create_sa_table(hf_path: Path, lower_bound_flags: bool = True) -> "pdt.DataFrame":
    """Creates a pandas dataframe with the sa parameters

    Args:
        hf_path: hdf5 filename, containing the hazard data
        lower_bound_flags: True includes the metadata for updating the lower bound hazard

    Returns:
        df: dataframe of sa parameters
    """
    site_list = list(extract_sites(hf_path).index)
    APoEs, hazard_rp_list = extract_APoEs(hf_path)
    quantile_list = extract_quantiles(hf_path)
    vs30_list = VS30_LIST

    log.info("begin calculate_parameter_arrays")
    PGA, Sas, PSV, Tc = calculate_parameter_arrays(hf_path)

    acc_spectra, imtls = extract_spectra(hf_path)

    log.info("begin fit_Td_array for mean Tds")
    mean_Td = fit_Td_array(
        PGA, Sas, Tc, acc_spectra, imtls, site_list, vs30_list, hazard_rp_list
    )

    log.info("begin create_mean_sa_table")
    mean_df = create_mean_sa_table(
        PGA, Sas, PSV, Tc, mean_Td, site_list, vs30_list, hazard_rp_list
    )

    log.info("begin update_lower_bound_sa")
    df = update_lower_bound_sa(
        mean_df,
        PGA,
        Sas,
        Tc,
        PSV,
        acc_spectra,
        imtls,
        vs30_list,
        hazard_rp_list,
        quantile_list,
    )

    df = replace_relevant_locations(df)

    if not lower_bound_flags:
        df = remove_lower_bound_metadata(df)

    return df
