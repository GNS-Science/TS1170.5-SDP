#! versioning.py
"""
This module defines data structures and input output utilities for the resource versions.


Classes:
    VersionInfo: dataclass defining the attributes of a NZSDDT version.
    VersionManager: manage the reading/writing of versions.



"""
import dataclasses
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import dacite
import nzshm_common

from ..config import RESOURCES_FOLDER

VERSION_LIST_FILENAME = "version_list.json"


def ensure_resource_folder(version_id: str, exist_ok: bool = False) -> Path:

    version_folder = Path(RESOURCES_FOLDER).parent / "resources" / f"v{version_id}"
    try:
        version_folder.mkdir(exist_ok=exist_ok)
    except (FileExistsError):
        raise FileExistsError(
            f"`{version_folder}` for version_id {version_id} already exists."
        )
    return version_folder


@dataclass(frozen=True)
class ConvertedFile:
    """
    A dataclass defining a converted file.

    NB not used from v2 on

    Args:
        input_filepath: path to the original file.
        output_filepath: path to the output file.
    """

    input_filepath: str
    output_filepath: str


@dataclass(frozen=True)
class IncludedFile:
    """
    A dataclass defining a resource file.

    Args:
        filepath: path to the file.
    """

    filepath: str


@dataclass(frozen=True)
class VersionInfo:
    """
    A dataclass defining the attributes of a NZSDDT version.

    Args:
        version_id: a unique version number.
        nzshm_model_version: the NSHM model version string.
        description: a versions description.
        conversions: a list of files converted (from AH to versioned) TODO: not used in v2.
        manifest: the files that make up the version
        nzshm_common_lib_version: the version of the nzshm_common library used to produce this version.
    """

    version_id: str = field(hash=True)
    nzshm_model_version: str  # nzshm_model.CURRENT_VERSION  # default to latest
    description: Optional[str] = None
    conversions: List[ConvertedFile] = field(default_factory=list)
    manifest: List[IncludedFile] = field(default_factory=list)
    nzshm_common_lib_version: str = nzshm_common.__version__

    def __str__(self):
        return f"version: {self.version_id}, model: {self.nzshm_model_version}, description: `{self.description}`"

    def resource_path(self, resource_folder: Optional[str] = None) -> Path:
        rf = resource_folder or RESOURCES_FOLDER
        return Path(rf) / f"v{self.version_id}"

    def collect_manifest(self):
        # update manifest
        resources = self.resource_path()
        for file in resources.iterdir():
            self.manifest.append(IncludedFile(str(file.relative_to(resources.parent))))


def standard_output_filename(version: Union[str, "VersionInfo"]):
    # print(type(version))
    if isinstance(version, VersionInfo):
        version = version.version_id
    return f"nzssdt_2023_v{version}.json.zip"


class VersionManager:
    """A class to manage the reading/writing of versions."""

    def __init__(self, resource_folder: Optional[str] = None):
        self._resource_folder = resource_folder or RESOURCES_FOLDER
        self._version_list_path = Path(self._resource_folder, VERSION_LIST_FILENAME)

    def read_version_list(self) -> Dict[str, VersionInfo]:
        """return the version list as a dict.

        Returns:
            version_dict: a dictionary of version info instances.
        """
        if not self._version_list_path.exists():
            raise RuntimeError(
                f"the version_list file {self._version_list_path} was not found."
            )
        version_list = json.load(open(self._version_list_path))
        version_dict = {}
        seen = []
        for vi in version_list:
            obj = dacite.from_dict(data_class=VersionInfo, data=vi)
            assert obj.version_id not in seen, "duplicate version id"
            version_dict[obj.version_id] = obj
            seen.append(obj.version_id)
        return version_dict

    def write_version_list(self, new_list: Iterable[VersionInfo]):
        """write the version list.

        Args:
            new_list: the list data to write to disk.
        """
        with open(self._version_list_path, "w") as fout:
            json.dump([dataclasses.asdict(vi) for vi in new_list], fout, indent=2)

    def get(self, version_id: str) -> Union[VersionInfo, None]:
        """get a version, given a valid id.

        Args:
            version_id: the version id string.

        Returns:
            version_info: the version info instance
        """
        versions = self.read_version_list()
        return versions.get(version_id)

    def add(self, version_info: VersionInfo):
        """add a version instance.

        Args:
            version_info: the version_info instance.

        Raises:
            KeyError: if the version_id already exists.
        """
        versions = self.read_version_list()
        if versions.get(version_info.version_id):
            raise (KeyError("Item already exists"))
        versions[version_info.version_id] = version_info
        self.write_version_list(list(versions.values()))

    def update(self, version_info: VersionInfo):
        """update a version instance.

        Args:
            version_info: the modified version instance.

        Raises:
            KeyError: if the version_id was not found
        """
        versions = self.read_version_list()
        current = versions.get(version_info.version_id, None)
        if not current:
            raise (KeyError)
        versions[version_info.version_id] = version_info
        self.write_version_list(versions.values())

    def remove(self, version_id: str) -> VersionInfo:
        """remove a version by version_id.

        Args:
            version_id: the version id string.

        Returns:
            version_info: the removed version info instance
        """
        versions = self.read_version_list()
        vi = versions.pop(version_id)
        self.write_version_list(versions.values())
        return vi


# def build_version_one(description: Optional[str] = None) -> VersionInfo:
#     """Write out the outputs and record everything in new VersionInfo
#
#     Args:
#         description: the description of the version.
#     """
#
#     vi = VersionInfo(
#         version_number=1, nzshm_model_version="NSHM_v1.0.4", description=description
#     )
#
#     # build SAT files
#     in_path = Path(
#         RESOURCES_FOLDER, "pipeline", "v1", "SaT-variables_v5_corrected-locations.pkl"
#     )
#     df = pd.read_pickle(in_path)
#     sat = SatTable(df)
#
#     # SAT named
#     out_path = Path(RESOURCES_FOLDER, "v1", "named_locations.json")
#     sat.named_location_df().to_json(
#         out_path,
#         index=False,
#         orient="table",
#         indent=2,
#         double_precision=3,
#     )
#     vi.conversions.append(
#         ConvertedFile(
#             input_filepath=str(in_path.relative_to(RESOURCES_FOLDER)),
#             output_filepath=str(out_path.relative_to(RESOURCES_FOLDER)),
#         )
#     )
#     vi.manifest.append(IncludedFile(str(out_path.relative_to(RESOURCES_FOLDER))))
#
#     # SAT gridded
#     out_path = Path(RESOURCES_FOLDER, "v1", "grid_locations.json")
#     sat.grid_location_df().to_json(
#         out_path,
#         index=False,
#         orient="table",
#         indent=2,
#         double_precision=3,
#     )
#     vi.conversions.append(
#         ConvertedFile(
#             input_filepath=str(in_path.relative_to(RESOURCES_FOLDER)),
#             output_filepath=str(out_path.relative_to(RESOURCES_FOLDER)),
#         )
#     )
#     vi.manifest.append(IncludedFile(str(out_path.relative_to(RESOURCES_FOLDER))))
#
#     # D&M
#     in_path = Path(RESOURCES_FOLDER, "pipeline", "v1", "D_and_M_with_floor.csv")
#     dandm = DistMagTable(in_path)
#
#     out_path = Path(RESOURCES_FOLDER, "v1", "d_and_m.json")
#     dandm.flatten().to_json(
#         out_path,
#         index=True,
#         orient="table",
#         indent=2,
#     )
#     vi.conversions.append(
#         ConvertedFile(
#             input_filepath=str(in_path.relative_to(RESOURCES_FOLDER)),
#             output_filepath=str(out_path.relative_to(RESOURCES_FOLDER)),
#         )
#     )
#     vi.manifest.append(IncludedFile(str(out_path.relative_to(RESOURCES_FOLDER))))
#
#     # add remaining unmodified files to the manifest
#     for infile in [
#         "major_faults.geojson",
#         "urban_area_polygons.geojson",
#     ]:
#         in_path = Path(RESOURCES_FOLDER, "v1", infile)
#         vi.manifest.append(IncludedFile(str(in_path.relative_to(RESOURCES_FOLDER))))
#
#     return vi
