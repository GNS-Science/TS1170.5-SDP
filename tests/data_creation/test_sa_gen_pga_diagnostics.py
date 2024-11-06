"""
PGA value diagnostics
"""

import pytest
from pytest_lazy_fixtures import lf

import nzssdt_2023.data_creation.constants as constants
import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen


@pytest.mark.parametrize(
    "site_class", [f"Site Class {sc}" for sc in "IV,V,VI".split(",")]
)
@pytest.mark.parametrize("city", ["Christchurch", "Dunedin", "Wellington", "Auckland",])
@pytest.mark.parametrize(
    "return_period, expected_pgas",
    [
        (2500, lf("pga_reduced_rp_2500")),
        # (500, lf("pga_reduced_rp_500")),
    ],
)
def test_create_sa_table_reduced_pga_diagnostic(
    mini_hcurves_hdf5_path, city, site_class, return_period, expected_pgas
):

    # df0 = sa_table_reduced
    # we need to drill into the create_sa_table method
    df0 = sa_gen.create_sa_table(mini_hcurves_hdf5_path)
    mini_hcurves_hdf5_path


    print(f'DIAG #5 the expected PGAs from Chris dlT csv files')
    print('=' * 40)
    df1 = expected_pgas
    expected_df = df1[df1["City"].isin(["Auckland", "Christchurch", "Dunedin", "Wellington",])]
    print(expected_df)
    print()

    assert pytest.approx(round(float(expected_df[expected_df["City"] == city][site_class]), 2)) == float(
        df0[(f"APoE: 1/{return_period}", site_class, "PGA")][city]
    )

# @pytest.mark.skip('WIP')
# @pytest.mark.parametrize(
#     "site_class", [f"Site Class {sc}" for sc in "IV,V,VI".split(",")]
# )
# @pytest.mark.parametrize("city", [ "Christchurch", "Dunedin", "Wellington"]) # "Auckland"
# @pytest.mark.parametrize(
#     "return_period, expected_pgas",
#     [
#         (2500, lf("pga_reduced_rp_2500")),
#         # (500, lf("pga_reduced_rp_500")),
#     ],
# )
# def test_expected_table_indexing_approah_anne_vs_chris(
#     mini_hcurves_hdf5_path, city, site_class, return_period, expected_pgas
# ):
#     # print(df1)
#     # expected_df = df1[df1["City"] == city]

#     # expected_df = expected_df.rename(
#     #     columns={
#     #         "SiteClass_IV": "Site Class IV",
#     #         "SiteClass_V": "Site Class V",
#     #         "SiteClass_VI": "Site Class VI",
#     #     }
#     # )

#     df_anne = df1.set_index('City')

#     print('expected_df')
#     print(expected_df)
#     print()
#     print('anne_df')
#     print(df_anne.loc[city,site_class])
#     print()
#     assert 0

