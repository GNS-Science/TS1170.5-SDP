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


def test_create_geojsons():
    # Mocking the create_geojson_files function
    def mock_create_geojson_files(polygons_path, faults_path, grid_path, override):
        pass

    pipeline_steps.create_geojson_files = mock_create_geojson_files
    pipeline_steps.create_geojsons(version="cbc", overwrite=True)
