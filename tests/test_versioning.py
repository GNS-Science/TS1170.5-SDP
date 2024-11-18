#! test_versioning.py

import nzshm_common
import nzshm_model
import pytest

from nzssdt_2023.versioning import VersionInfo, standard_output_filename


@pytest.fixture(scope="module")
def version_info_fixture():
    V = 5
    return VersionInfo(
        version_id=V,
        nzshm_model_version=nzshm_model.CURRENT_VERSION,  # nzshm_model.CURRENT_VERSION  # default to latest
        # nzshm_common_lib_version = nzshm_common.__version__
        # nzshm_model_lib_version = nzshm_model.__version__
        # input_filename="ABC",
        # output_filename=standard_output_filename(V),
    )


def test_standard_filename_from_number():
    assert standard_output_filename(5) == "nzssdt_2023_v5.json.zip"


def test_standard_filename_from_version_info(version_info_fixture):
    assert standard_output_filename(version_info_fixture) == "nzssdt_2023_v5.json.zip"


class TestVersionInfo(object):
    def test_add_version(self, version_info_fixture):
        nv = version_info_fixture

        assert nv.description is None
        assert nv.nzshm_common_lib_version == nzshm_common.__version__
        assert nv.nzshm_model_lib_version == nzshm_model.__version__
        assert nv.nzshm_model_version == nzshm_model.CURRENT_VERSION
