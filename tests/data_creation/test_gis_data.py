"""
test gis data versus v1 fixtures

"""
import pytest
import geopandas as gpd

from io import StringIO
from nzssdt_2023.data_creation.gis_data import cleanup_polygon_gpd, filter_cfm_by_sliprate, build_d_value_dataframe
from nzssdt_2023.data_creation.constants import POLYGON_PATH, CFM_URL, LOCATION_REPLACEMENTS


def test_polygons(polygons_v1):

    polygons = cleanup_polygon_gpd(POLYGON_PATH).reset_index()

    assert all(polygons == polygons_v1)


def test_faults(faults_v1):

    faults = filter_cfm_by_sliprate(CFM_URL)

    assert all(faults[['Name','geometry']] == faults_v1[['Name','geometry']])


# test generated D values against v1 fixture
def test_D_values_against_v1(dandm_v1):

    # remove v1 locations that don't have their own polygon
    replaced_locations = []
    for location in LOCATION_REPLACEMENTS:
        for replaced_location in LOCATION_REPLACEMENTS[location].replaced_locations:
            replaced_locations.append(replaced_location)
    dandm_v1.drop(replaced_locations, axis=0, inplace=True)

    # generate new D values
    D_values = build_d_value_dataframe()

    # Hamilton and Te Puke are flipped. Confirm that there is no difference in the index sets
    assert list(dandm_v1.index.difference(D_values.index)) == []
    assert list(D_values.index.difference(dandm_v1.index)) == []

    # confirm that the reordered D values are the same
    assert D_values.loc[dandm_v1.index,'D'].equals(dandm_v1['D'])

