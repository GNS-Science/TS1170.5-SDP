"""
test gis data versus v1 fixtures

note: the grid points geodataframe so it is tested against a new expected gdf

"""

from nzssdt_2023.data_creation.constants import (
    CFM_URL,
    LOCATION_REPLACEMENTS,
    POLYGON_PATH,
)
from nzssdt_2023.data_creation.gis_data import (
    build_d_value_dataframe,
    cleanup_polygon_gpd,
    filter_cfm_by_sliprate,
    create_grid_gpd,
)


def test_polygons(polygons_v1):

    polygons = cleanup_polygon_gpd(POLYGON_PATH).reset_index()

    assert all(polygons == polygons_v1)


def test_faults(faults_v1):

    faults = filter_cfm_by_sliprate(CFM_URL)

    assert all(faults[["Name", "geometry"]] == faults_v1[["Name", "geometry"]])


def test_grid_points(grid_points_expected):

    grid_points = create_grid_gpd().reset_index()

    assert all(grid_points == grid_points_expected)


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
    assert D_values.loc[dandm_v1.index, "D"].equals(dandm_v1["D"])
