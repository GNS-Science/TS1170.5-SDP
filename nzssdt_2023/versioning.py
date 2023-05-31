#! versioning.py
"""Define data structure and input output utilities for the resource versions."""

from dataclasses import dataclass, field
from typing import Union

import nzshm_common
import nzshm_model

# from . import RESOURCES_FOLDER


def standard_output_filename(version: Union[int, "VersionInfo"]):
    # print(type(version))
    if isinstance(version, VersionInfo):
        version = version.version_number
    return f"nzssdt_2023_v{version}.json.zip"


@dataclass(frozen=True)
class VersionInfo:
    version_number: int = field(hash=True)
    nzshm_model_version: str  # nzshm_model.CURRENT_VERSION  # default to latest
    input_filename: str
    output_filename: str
    description: Union[str, None] = None
    nzshm_common_lib_version: str = nzshm_common.__version__
    nzshm_model_lib_version: str = nzshm_model.__version__
