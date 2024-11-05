"""
test the uhs_value function in `nzssdt_2023.data_creation.sa_parameter_generation`
"""

from collections import namedtuple

import numpy as np
import pytest

import nzssdt_2023.data_creation.sa_parameter_generation as sa_gen


# this is my first, exploratory test, which has been replicated un the parametrized test below
def test_uhs_value_python_exploratory():
    assert sa_gen.uhs_value(1.0, 1.0, 1.0, 1.0, 1.0) == 1.0
    assert sa_gen.uhs_value(2.0, 2.0, 2.0, 2.0, 2.0) == 2.0
    assert (
        sa_gen.uhs_value(period=0, PGA=2.233, Sas=2.0, Tc=2.0, Td=2.0) == 2.233
    ), "period 0"
    assert (
        sa_gen.uhs_value(period=0.001, PGA=2.0, Sas=1.5, Tc=2.0, Td=2.0) == 1.995
    ), "small period"
    assert (
        sa_gen.uhs_value(period=0.5, PGA=2.0, Sas=1.5, Tc=2.0, Td=2.0) == 1.5
    ), "period < Tc"
    assert (
        sa_gen.uhs_value(period=0.5, PGA=2.0, Sas=1.5, Tc=0.45, Td=2.0)
        == 1.5 * 0.45 / 0.5
    ), "period < Td:"
    assert (
        sa_gen.uhs_value(period=5.0, PGA=2.0, Sas=1.5, Tc=0.45, Td=2.0)
        == 1.5 * (0.45 / 5.0) * (2.0 / 5.0) ** 0.5
    ), "everything else"


UhsArgs = namedtuple("UhsArgs", "period, PGA, Sas, Tc, Td")

UHS_EXPECTED = [
    pytest.param(UhsArgs(1.0, 1.0, 1.0, 1.0, 1.0), 1.0, id="default"),
    pytest.param(
        UhsArgs(period=0, PGA=2.233, Sas=2.0, Tc=2.0, Td=2.0), 2.233, id="period==0"
    ),
    pytest.param(
        UhsArgs(period=0.001, PGA=2.0, Sas=1.5, Tc=2.0, Td=2.0),
        1.995,
        id="period < 0.1",
    ),
    pytest.param(
        UhsArgs(period=0.5, PGA=2.0, Sas=1.5, Tc=2.0, Td=2.0), 1.5, id="period < Tc"
    ),
    pytest.param(
        UhsArgs(period=0.5, PGA=2.0, Sas=1.5, Tc=0.45, Td=2.0),
        1.5 * 0.45 / 0.5,
        id="period < Td",
    ),
    pytest.param(
        UhsArgs(period=5.0, PGA=2.0, Sas=1.5, Tc=0.45, Td=2.0),
        1.5 * (0.45 / 5.0) * (2.0 / 5.0) ** 0.5,
        id="otherwise",
    ),
]


@pytest.mark.parametrize("args, expected", UHS_EXPECTED)
def test_uhs_value_python_parameterized(args, expected):
    assert sa_gen.uhs_value(**args._asdict()) == expected


@pytest.mark.parametrize("args, expected", UHS_EXPECTED)
def test_uhs_value_numpy(args, expected):

    # This test reproduces what's done in sa_gen module when calling ush_value
    # But could we0 write this so the array is passed in  rather than unpacking
    # with ... `for period in periods`?
    # See TODO notes in function body

    periods = np.ndarray([1, 1])
    periods.fill(args.period)

    res = [
        sa_gen.uhs_value(period, args.PGA, args.Sas, args.Tc, args.Td)
        for period in periods
    ]
    print(res)
    assert res[0] == expected
