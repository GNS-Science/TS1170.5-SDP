#! test_version_info.py

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
    assert "v1/named_locations.json" in str(vi.manifest)
    assert "v1/grid_locations.json" in str(vi.manifest)
    assert "v1/d_and_m.json" in str(vi.manifest)


def test_collect_manifest():
    vi = VersionInfo("2", "B")
    vi.collect_manifest()
    assert "v2/named_locations_combo.json" in str(vi.manifest)
