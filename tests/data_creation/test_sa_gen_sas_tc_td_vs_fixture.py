"""
Sas, Tc, Td values vs external fixtures

 - functions in `nzssdt_2023.data_creation.sa_parameter_generation`
 - fixtures in testsw/fixtures/sas-tc-td_parameters

"""

import pytest
from conftest import sas_tc_td_parameters
from nzssdt_2023.data_creation import sa_parameter_generation as sa_gen

@pytest.mark.parametrize("site", ["Auckland", "Christchurch", "Dunedin", "Wellington"])
@pytest.mark.parametrize("return_period", ["25", "50", "100", "250", "500", "1000", "2500"])
@pytest.mark.parametrize("sc", ["I", "II", "III", "IV", 'V', 'VI'])
@pytest.mark.parametrize("parameter", ["Sas", "Tc", "Td"])
def test_parameter_table(site,return_period,sc,parameter,sas_tc_td_parameters,output_table_mini):
    """Test the generated output table against fixture values."""

    if parameter=='PGA':
        assert 0  # this fixture should only be used to test Sas, Tc, and Td
    elif parameter=='Sas':
        fix_col = f'Sa,s Class {sc} (g)'
        if fix_col not in sas_tc_td_parameters[return_period].columns:
            fix_col = f'Sa,s Class {sc}  (g)'  # fixture was created with a spacing error in the labels
    else:
        fix_col = f'{parameter} Class {sc} (s)'

    output_col = (f'APoE: 1/{return_period}',f'Site Class {sc}', parameter)

    assert sas_tc_td_parameters[return_period].loc[site,fix_col]==round(output_table_mini.loc[site,output_col],5)



