#! versioning.py
"""
Dataclasses defining structures for versioning.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import nzshm_common

from ..config import REPORTS_FOLDER, RESOURCES_FOLDER


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
        manifest: the data files used for reporting
        reports: the reports files csv and PDF
        nzshm_common_lib_version: the version of the nzshm_common library used to produce this version.
    """

    version_id: str = field(hash=True)
    nzshm_model_version: str  # nzshm_model.CURRENT_VERSION  # default to latest
    description: Optional[str] = None
    conversions: List[ConvertedFile] = field(default_factory=list)  # not used after v1
    manifest: List[IncludedFile] = field(default_factory=list)
    reports: List[IncludedFile] = field(default_factory=list)
    nzshm_common_lib_version: str = nzshm_common.__version__

    def __str__(self):
        return f"version: {self.version_id}, model: {self.nzshm_model_version}, description: `{self.description}`"

    def resource_path(self, resource_folder: Optional[str] = None) -> Path:
        rf = resource_folder or RESOURCES_FOLDER
        return Path(rf) / f"v{self.version_id}"

    def reports_path(self, reports_folder: Optional[str] = None) -> Path:
        rf = reports_folder or REPORTS_FOLDER
        return Path(rf) / f"v{self.version_id}"

    def collect_manifest(self):
        # update manifest
        resources = self.resource_path()
        for file in resources.iterdir():
            self.manifest.append(
                IncludedFile(str(file.relative_to(resources.parent.parent)))
            )

        reports = self.reports_path()
        for file in reports.iterdir():
            self.reports.append(
                IncludedFile(str(file.relative_to(reports.parent.parent)))
            )
