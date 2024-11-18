import pytest  # noqa
from click.testing import CliRunner

from nzssdt_2023.scripts import version_cli  # module reference for patching
from nzssdt_2023.scripts.version_cli import cli as version

### the actual tests ...


def test_ls():
    runner = CliRunner()
    result = runner.invoke(version, ["ls"])
    assert result.exit_code == 0
    assert "1" in result.output


def test_ls_verbose():
    runner = CliRunner()
    result = runner.invoke(version, ["ls", "--verbose"])
    assert result.exit_code == 0
    assert "1, NSHM_v1.0.4" in result.output


def test_init_verbose(mocker):

    # patch the underlying functions
    vi_og = version_cli.VersionInfo("MY_NEW_VER", "NSHM_v99")
    vi_new = version_cli.VersionInfo("MY_NEW_ONE", "NSHM_v00")

    mocked_read_version_list = mocker.patch.object(
        version_cli.version_manager, "read_version_list", return_value=[vi_og]
    )
    mocked_write_version_list = mocker.patch.object(
        version_cli.version_manager, "write_version_list", return_value=[vi_new]
    )

    runner = CliRunner()
    result = runner.invoke(
        version, ["init", "MY_NEW_ONE", "-N", "NSHM_v00", "--verbose"]
    )

    mocked_read_version_list.assert_called_once()
    mocked_write_version_list.assert_called_once_with([vi_og, vi_new])

    print(result.output)

    assert result.exit_code == 0
    assert f"VersionInfo(version_id='{vi_new.version_id}'" in result.output
    assert f"nzshm_model_version='{vi_new.nzshm_model_version}'" in result.output


def test_info(mocker):

    # patch the underlying functions
    vi_og = version_cli.VersionInfo("MY_NEW_VER", "NSHM_v99")
    vi_new = version_cli.VersionInfo("MY_NEW_ONE", "NSHM_v00")

    mocked_read_version_list = mocker.patch.object(
        version_cli.version_manager, "read_version_list", return_value=[vi_og, vi_new]
    )

    runner = CliRunner()
    result = runner.invoke(version, ["info", "MY_NEW_ONE"])

    mocked_read_version_list.assert_called_once()
    print(result.output)
    assert result.exit_code == 0
    assert str(vi_new) in result.output
