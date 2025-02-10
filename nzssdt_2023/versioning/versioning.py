#! versioning.py
"""
This module provides tools for managing resource versions.

Classes:
    VersionManager: manage the reading/writing of versions.

"""

import dacite
import dataclasses
import json
from pathlib import Path
from typing import Dict, Iterable, Optional, Union


from ..config import RESOURCES_FOLDER
from .dataclass import VersionInfo

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
