"""
test the pga functions in `nzssdt_2023.data_creation.sa_parameter_generation`
"""

#import pytest

import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen

def test_inspect_create_sa_table(mini_hcurves_hdf5_path, pga_adjusted_rp_2500):
    site_list = list(sa_gen.extract_sites(mini_hcurves_hdf5_path).index)

    print(site_list) #  ['Auckland', 'Christchurch', 'Dunedin', 'Wellington']
    assert len(site_list) == 4

    print('pga_adjusted', pga_adjusted_rp_2500)

    APoEs, hazard_rp_list = sa_gen.extract_APoEs(mini_hcurves_hdf5_path)

    print('APoEs', APoEs)
    print()
    print('hazard_rp_list', hazard_rp_list)
    print()

    quantile_list = sa_gen.extract_quantiles(mini_hcurves_hdf5_path)
    print('quantile_list', quantile_list)
    print()


def test_create_sa_table(mini_hcurves_hdf5_path, pga_adjusted_rp_2500):

    sa_table = sa_gen.create_sa_table(mini_hcurves_hdf5_path)

    print(sa_table)
    assert 0



