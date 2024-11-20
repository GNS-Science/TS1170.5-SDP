import pytest  # noqa

from nzssdt_2023.versioning import VersionInfo

#     read_version_list,  # noqa
#     write_version_list,
# )


@pytest.fixture(scope="module")
def version_info_fixture():
    V = "5"
    return VersionInfo(
        version_id=V,
        nzshm_model_version="NSHM_v1.0.4"
        # nzshm_common_lib_version = nzshm_common.__version__
        # nzshm_model_lib_version = nzshm_model.__version__
        # input_filename="ABC",
        # output_filename=standard_output_filename(V),
    )
