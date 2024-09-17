#! versioning.py
"""Define data structure and input output utilities for the resource versions."""
import dataclasses
import json
import pathlib
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Union

import dacite
import nzshm_common
import nzshm_model

from . import RESOURCES_FOLDER

VERSION_LIST_FILENAME = "version_list.json"


def standard_output_filename(version: Union[int, "VersionInfo"]):
    # print(type(version))
    if isinstance(version, VersionInfo):
        version = version.version_number
    return f"nzssdt_2023_v{version}.json.zip"


@dataclass(frozen=True)
class ConvertedFile:
    input_filepath: str
    output_filepath: str


@dataclass(frozen=True)
class IncludedFile:
    filepath: str


@dataclass(frozen=True)
class VersionInfo:
    version_number: int = field(hash=True)
    nzshm_model_version: str  # nzshm_model.CURRENT_VERSION  # default to latest
    description: Optional[str] = None
    conversions: List[ConvertedFile] = field(default_factory=list)
    manifest: List[IncludedFile] = field(default_factory=list)
    nzshm_common_lib_version: str = nzshm_common.__version__
    nzshm_model_lib_version: str = nzshm_model.__version__


def read_version_list():
    """returns the current version list."""
    vl = pathlib.Path(RESOURCES_FOLDER, VERSION_LIST_FILENAME)
    if not vl.exists():
        return []
    version_list = json.load(open(vl))
    return [dacite.from_dict(data_class=VersionInfo, data=vi) for vi in version_list]


def write_version_list(new_list: Iterable[VersionInfo]):
    """creates/updates the version list."""
    vl = pathlib.Path(RESOURCES_FOLDER, VERSION_LIST_FILENAME)
    with open(vl, "w") as fout:
        json.dump([dataclasses.asdict(vi) for vi in new_list], fout, indent=2)
