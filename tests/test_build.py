#! test_build.py

import pathlib
import shutil

from nzssdt_2023.config import RESOURCES_FOLDER
from nzssdt_2023.build import build_version_one

clone_files = ["major_faults.geojson", "urban_area_polygons.geojson"]
new_files = ["d_and_m.json", "grid_locations.json", "named_locations.json"]


def prepare_temp_inputs(temporary_dir):
    input_folder = pathlib.Path(RESOURCES_FOLDER, "pipeline", "v1")
    tmp_folder = pathlib.Path(temporary_dir, "pipeline", "v1")
    shutil.copytree(input_folder, tmp_folder)  # Will fail if `foo` exists


def prepare_temp_clones(temporary_dir):
    input_folder = pathlib.Path(RESOURCES_FOLDER, "v1")
    tmp_folder = pathlib.Path(temporary_dir, "v1")
    tmp_folder.mkdir()
    for fname in clone_files:
        shutil.copy(input_folder / fname, tmp_folder / fname)


def test_build_version_one(tmp_path):

    print(tmp_path)

    prepare_temp_inputs(tmp_path)
    prepare_temp_clones(tmp_path)

    import nzssdt_2023.build  # monkey patch the file location

    ORES = nzssdt_2023.build.RESOURCES_FOLDER
    nzssdt_2023.build.RESOURCES_FOLDER = pathlib.Path(tmp_path)

    build_version_one()

    # all the files exist ...
    for name in clone_files + new_files:
        assert pathlib.Path(tmp_path / "v1" / name).exists()

    nzssdt_2023.build.RESOURCES_FOLDER = ORES
