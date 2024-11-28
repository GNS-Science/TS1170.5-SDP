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


@dataclass(frozen=True)
class ConvertedFile:
    """
    A dataclass defining a converted file.

    NB maybe deprecatable

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
        conversions: a list of files converted (from AH to versioned) TODO: maybe deprecatable.
        manifest: the files that make up the version
        nzshm_common_lib_version: the version of the nzshm_common library used to produce this version.
    """

    version_id: str = field(hash=True)
    nzshm_model_version: str  # nzshm_model.CURRENT_VERSION  # default to latest
    description: Optional[str] = None
    conversions: List[ConvertedFile] = field(default_factory=list)
    manifest: List[IncludedFile] = field(default_factory=list)
    nzshm_common_lib_version: str = nzshm_common.__version__


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
