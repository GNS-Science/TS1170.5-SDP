#! versioning.py
"""
This module defines data structures and input output utilities for the resource versions.

"""
import dataclasses
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Union

import dacite
import nzshm_common
import nzshm_model

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
    A dataclass defining a resoource file.

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
        nzshm_model_version: the NSHM mode version string.
        description: a versions description.
        conversions: a list of files converted (from AH to versioned) TODO: maybe deprecatable.
        manifest: the files that make up the version
        nzshm_common_lib_version: the version of the nzshm_common library used to produce this version.
        nzshm_model_lib_version: the version of the nzshm_model library used to produce this version.
    """

    version_id: str = field(hash=True)
    nzshm_model_version: str  # nzshm_model.CURRENT_VERSION  # default to latest
    description: Optional[str] = None
    conversions: List[ConvertedFile] = field(default_factory=list)
    manifest: List[IncludedFile] = field(default_factory=list)
    nzshm_common_lib_version: str = nzshm_common.__version__
    nzshm_model_lib_version: str = nzshm_model.__version__


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

    def read_version_list(self):
        """returns the current version list."""
        if not self._version_list_path.exists():
            raise RuntimeError(
                f"the version_list file {self._version_list_path} was not found."
            )
        version_list = json.load(open(self._version_list_path))
        return [
            dacite.from_dict(data_class=VersionInfo, data=vi) for vi in version_list
        ]

    def write_version_list(self, new_list: Iterable[VersionInfo]):
        """creates/updates the version list."""
        with open(self._version_list_path, "w") as fout:
            json.dump([dataclasses.asdict(vi) for vi in new_list], fout, indent=2)
