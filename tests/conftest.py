import itertools

import pytest

import nzssdt_2023.data_creation.dm_parameter_generation as dm_parameter_generation
import nzssdt_2023.data_creation.mean_magnitudes as mean_magnitudes


def mock_get_mean_mags(
    hazard_id,
    locations,
    vs30s,
    imts,
    poes,
    hazard_agg,
):
    for location, vs30, imt, poe in itertools.product(locations, vs30s, imts, poes):
        _, name = mean_magnitudes.get_loc_id_and_name(location.downsample(0.001).code)
        yield dict(
            name=name,
            poe=poe,
            mag=5.0,
        )


@pytest.fixture
def mean_mags_fixture(monkeypatch):
    monkeypatch.setattr(mean_magnitudes, "get_mean_mags", mock_get_mean_mags)


@pytest.fixture(scope="function")
def workingfolder_fixture(monkeypatch, tmp_path):
    monkeypatch.setattr(dm_parameter_generation, "WORKING_FOLDER", str(tmp_path))
