import pandas as pd
import pytest

from nzssdt_2023.scripts import pipeline_steps


# Test cases for pipeline_steps module
def test_hf_filepath():
    assert (
        str(pipeline_steps.hf_filepath(site_limit=10)) == "/tmp/first_20_hcurves.hdf5"
    )
    assert str(pipeline_steps.hf_filepath()) == "/tmp/all_hcurves.hdf5"


def test_get_site_list():
    sites = pipeline_steps.get_site_list(site_limit=12)
    assert sites.shape == (25, 3)  # Note 25 rows, because "Auckland" is always added

    akl = sites.loc["Auckland"]
    assert akl.latlon == "-36.852~174.763"
    assert akl.lat == "-36.852"
    assert akl.lon == "174.763"


def test_get_hazard_curves():
    # Mocking the query_NSHM_to_hdf5 function
    def mock_query_NSHM_to_hdf5(hf_path, hazard_id, site_list, site_limit):
        pass

    pipeline_steps.query_NSHM_to_hdf5 = mock_query_NSHM_to_hdf5
    pipeline_steps.get_hazard_curves(site_list=["site1"], site_limit=2)


def test_get_resources_version_path():
    respath = pipeline_steps.get_resources_version_path("cbc")
    assert respath.name == "vcbc"


@pytest.mark.skip("WIP")
def test_build_json_tables():
    # Mocking the necessary functions
    def mock_create_sa_table(hf_path):
        return pd.DataFrame({"sa": [1, 2]})

    def mock_D_and_M_df(site_list, rp_list):
        return pd.DataFrame({"dm": [1, 2]})

    pipeline_steps.sa_gen.create_sa_table = mock_create_sa_table
    pipeline_steps.dm_gen.create_D_and_M_df = mock_D_and_M_df

    # Mocking the to_standard_json function
    def mock_to_standard_json(df, path):
        pass

    pipeline_steps.to_standard_json = mock_to_standard_json

    pipeline_steps.build_json_tables(
        hf_path="path/to/hdf5",
        site_list=["site1"],
        version="cbc",
        site_limit=2,
        overwrite_json=True,
    )


def test_create_geojsons():
    # Mocking the create_geojson_files function
    def mock_create_geojson_files(polygons_path, faults_path, override):
        pass

    pipeline_steps.create_geojson_files = mock_create_geojson_files

    pipeline_steps.create_geojsons(version="cbc", overwrite=True)


@pytest.mark.skip("WIP")
def test_create_parameter_tables():
    # Mocking the necessary functions
    def mock_get_hazard_curves(site_list, site_limit, hazard_id):
        pass

    def mock_build_json_tables(hf_path, site_list, version, site_limit, overwrite_json):
        pass

    pipeline_steps.get_hazard_curves = mock_get_hazard_curves
    pipeline_steps.build_json_tables = mock_build_json_tables

    # Mocking the to_standard_json function
    def mock_to_standard_json(df, path):
        pass

    pipeline_steps.to_standard_json = mock_to_standard_json

    pipeline_steps.create_parameter_tables(
        version="cbc", site_limit=5, no_cache=True, overwrite_json=True
    )
