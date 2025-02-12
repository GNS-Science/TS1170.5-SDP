import pytest  # noqa
from click.testing import CliRunner

from nzssdt_2023.scripts import (
    pipeline_cli as version_cli,
)  # module reference for patching
from nzssdt_2023.scripts.pipeline_cli import cli
from nzssdt_2023.versioning import VersionInfo


@pytest.mark.parametrize("options", [None, "--verbose"])
def test_ls(options):
    runner = CliRunner()
    cmdline = ["ls"]
    if options:
        cmdline += options.split(" ")
    result = runner.invoke(cli, cmdline)
    assert result.exit_code == 0
    assert "1" in result.output

    if options and "--verbose" in options:
        assert "1, NSHM_v1.0.4" in result.output


@pytest.mark.parametrize("options", [None, "--verbose"])
def test_publish(mocker, options):
    version_manager = version_cli.version_manager

    # patch the underlying functions
    vi_og = VersionInfo("MY_NEW_VER", "NSHM_v99")
    vi_new = VersionInfo(
        "MY_NEW_ONE", "NSHM_v00", description="Read all about the new one"
    )

    mocked_vi_collect = mocker.patch.object(
        VersionInfo, "collect_manifest", return_value=[]
    )
    mocked_read_version_list = mocker.patch.object(
        version_manager, "read_version_list", return_value={vi_og.version_id: vi_og}
    )
    mocked_write_version_list = mocker.patch.object(
        version_manager, "write_version_list", return_value={vi_new.version_id: vi_new}
    )

    runner = CliRunner()

    cmdline = ["06-publish", "MY_NEW_ONE", "NSHM_v00", "Read all about the new one"]
    if options:
        cmdline += options.split(" ")
    result = runner.invoke(cli, cmdline)

    print(result.output)
    assert result.exit_code == 0

    mocked_read_version_list.assert_called_once()
    mocked_vi_collect.assert_called_once()
    mocked_write_version_list.assert_called_once_with([vi_og, vi_new])

    print(result.output)

    if options and "--verbose" in options:
        assert vi_new.version_id in result.output
        assert vi_new.nzshm_model_version in result.output
        assert vi_new.description in result.output

    if options and "--verbose" in options and "--merge" not in options:
        assert "Wrote new version" in result.output


@pytest.mark.parametrize("options", [None, "--verbose"])
def test_01_init(mocker, options):
    mock_ensure_resource_folders = mocker.patch.object(
        version_cli, "ensure_resource_folders"
    )

    runner = CliRunner()
    cmdline = ["01-init", "MY_NEW_ONE"]
    if options:
        cmdline += options.split(" ")
    result = runner.invoke(cli, cmdline)

    print(result.output)
    assert result.exit_code == 0

    mock_ensure_resource_folders.assert_called_once_with("MY_NEW_ONE")

    if options and "--verbose" in options:
        assert "init resource for version_id: MY_NEW_ONE" in result.output


@pytest.mark.parametrize("options", [None, "--verbose"])
def test_02_hazard(mocker, options):
    mock_ensure_resource_folders = mocker.patch.object(
        version_cli, "ensure_resource_folders"
    )

    runner = CliRunner()
    cmdline = ["01-init", "MY_NEW_ONE"]
    if options:
        cmdline += options.split(" ")
    result = runner.invoke(cli, cmdline)

    print(result.output)
    assert result.exit_code == 0

    mock_ensure_resource_folders.assert_called_once_with("MY_NEW_ONE")

    if options and "--verbose" in options:
        assert "init resource for version_id: MY_NEW_ONE" in result.output


def test_info(mocker):
    version_manager = version_cli.version_manager
    # patch the underlying functions
    vi_og = version_cli.VersionInfo("MY_NEW_VER", "NSHM_v99", description="about me")

    mocked_read_version_list = mocker.patch.object(
        version_manager, "read_version_list", return_value={vi_og.version_id: vi_og}
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["info", "MY_NEW_VER"])

    mocked_read_version_list.assert_called_once()
    print(result.output)
    assert result.exit_code == 0
    assert str(vi_og) in result.output
    assert vi_og.version_id in result.output
    assert vi_og.nzshm_model_version in result.output
    assert vi_og.description in result.output
