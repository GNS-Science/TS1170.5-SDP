#! test_version_info.py

from pathlib import Path

import nzshm_common

from nzssdt_2023.versioning import VersionInfo


def test_init():
    vi = VersionInfo("A", "B")
    assert vi.version_id == "A"
    assert vi.nzshm_model_version == "B"
    assert vi.description is None
    assert vi.nzshm_common_lib_version == nzshm_common.__version__


def test_collect_manifest_v1():
    vi = VersionInfo("1", "B")
    vi.collect_manifest()
    # under Windows we can't just say str(vi.manifest) because that will double-encode backslashes
    included = str(" ".join([x.filepath for x in vi.manifest]))
    assert str(Path("v1") / "named_locations.json") in included
    assert str(Path("v1") / "grid_locations.json") in included
    assert str(Path("v1") / "d_and_m.json") in included


def test_collect_manifest():
    vi = VersionInfo("2", "B")
    vi.collect_manifest()
    included = str(" ".join([x.filepath for x in vi.manifest]))
    assert str(Path("v2") / "named_locations_combo.json") in included
