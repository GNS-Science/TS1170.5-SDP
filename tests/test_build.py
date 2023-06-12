#! test_build.py

import os
import pathlib
import shutil
import tempfile

from nzssdt_2023 import RESOURCES_FOLDER
from nzssdt_2023.build import build_version_one

TEMP_DIR = str(tempfile.TemporaryDirectory().name)
clone_files = ["major_faults.geojson", "urban_area_polygons.geojson"]
new_files = ["d_and_m.json", "grid_locations.json", "named_locations.json"]


def prepare_temp_inputs():
    input_folder = pathlib.Path(RESOURCES_FOLDER, "input", "v1")
    tmp_folder = pathlib.Path(TEMP_DIR, "input", "v1")
    shutil.copytree(input_folder, tmp_folder)  # Will fail if `foo` exists


def prepare_temp_clones():
    input_folder = pathlib.Path(RESOURCES_FOLDER, "v1")
    tmp_folder = pathlib.Path(TEMP_DIR, "v1")
    os.mkdir(str(tmp_folder))
    for fname in clone_files:
        shutil.copy(input_folder / fname, tmp_folder / fname)


def test_build_version_one():

    print(TEMP_DIR)

    prepare_temp_inputs()
    prepare_temp_clones()

    import nzssdt_2023.build  # monkey patch the file location

    ORES = nzssdt_2023.build.RESOURCES_FOLDER
    nzssdt_2023.build.RESOURCES_FOLDER = pathlib.Path(TEMP_DIR)

    build_version_one()

    # all the files exist ...
    with pathlib.Path(TEMP_DIR) as tf:
        for name in clone_files + new_files:
            assert pathlib.Path(tf / "v1" / name).exists()

    nzssdt_2023.build.RESOURCES_FOLDER = ORES
