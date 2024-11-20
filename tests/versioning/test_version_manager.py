#! test_versioning.py

from dataclasses import asdict

import pytest

from nzssdt_2023.versioning import VersionInfo, VersionManager


def test_version_manager_get(mocker):

    # patch the underlying functions
    vi_og = VersionInfo("MY_NEW_VER", "NSHM_v99")
    version_manager = VersionManager()

    mocked_read_version_list = mocker.patch.object(
        version_manager, "read_version_list", return_value={vi_og.version_id: vi_og}
    )

    res = version_manager.get(vi_og.version_id)
    mocked_read_version_list.assert_called_once()
    assert res == vi_og
    mocked_read_version_list.reset_mock()

    res = version_manager.get("NON")
    mocked_read_version_list.assert_called_once()
    assert res is None


def test_version_manager_update(mocker):

    version_manager = VersionManager()
    vi_og = VersionInfo("MY_NEW_VER", "NSHM_v99")
    vi_new = VersionInfo("MY_NEW_ONE", "NSHM_v00")

    # patch the underlying functions
    mocked_read_version_list = mocker.patch.object(
        version_manager, "read_version_list", return_value={vi_og.version_id: vi_og}
    )
    mocked_write_version_list = mocker.patch.object(
        version_manager, "write_version_list", return_value={vi_new.version_id: vi_new}
    )

    vi_dict = asdict(version_manager.get(vi_og.version_id))
    vi_dict["nzshm_model_version"] = "NEWMODEL"
    vi_mod = VersionInfo(**vi_dict)
    mocked_read_version_list.assert_called_once()
    mocked_read_version_list.reset_mock()

    version_manager.update(vi_mod)
    mocked_read_version_list.assert_called_once()
    mocked_write_version_list.assert_called_once()

    assert vi_mod == version_manager.get(vi_mod.version_id)


def test_version_manager_update_miss(mocker):

    version_manager = VersionManager()
    vi_og = VersionInfo("MY_NEW_VER", "NSHM_v99")

    # patch the underlying functions
    mocked_read_version_list = mocker.patch.object(
        version_manager, "read_version_list", return_value={vi_og.version_id: vi_og}
    )

    print(dir(vi_og))
    vi_dict = asdict(version_manager.get(vi_og.version_id))
    vi_dict["version_id"] = "BADID"
    vi_mod = VersionInfo(**vi_dict)
    mocked_read_version_list.assert_called_once()
    mocked_read_version_list.reset_mock()

    with pytest.raises(KeyError):
        version_manager.update(vi_mod)
    mocked_read_version_list.assert_called_once()


def test_version_manager_add(mocker):
    version_manager = VersionManager()
    vi_new = VersionInfo("MY_NEW_VER", "NSHM_v99")

    # patch the underlying functions
    mocked_read_version_list = mocker.patch.object(
        version_manager, "read_version_list", return_value={}
    )
    mocked_write_version_list = mocker.patch.object(
        version_manager, "write_version_list", return_value={vi_new.version_id: vi_new}
    )

    version_manager.add(vi_new)
    mocked_read_version_list.assert_called_once()
    mocked_write_version_list.assert_called_once()

    with pytest.raises(KeyError):
        version_manager.add(vi_new)
    mocked_read_version_list.assert_called()


def test_version_manager_remove(mocker):
    version_manager = VersionManager()
    vi_og = VersionInfo("MY_NEW_VER", "NSHM_v99")

    # patch the underlying functions
    mocked_read_version_list = mocker.patch.object(
        version_manager, "read_version_list", return_value={vi_og.version_id: vi_og}
    )
    mocked_write_version_list = mocker.patch.object(
        version_manager, "write_version_list", return_value={}
    )

    og = version_manager.remove(vi_og.version_id)
    mocked_read_version_list.assert_called_once()
    mocked_write_version_list.assert_called_once()

    assert og == vi_og

    with pytest.raises(KeyError):
        version_manager.remove(vi_og.version_id)
