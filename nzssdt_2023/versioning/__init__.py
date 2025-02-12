"""
this package contains the versioning features for the library.

"""
from .dataclass import ConvertedFile, IncludedFile, VersionInfo
from .versioning import (
    VersionManager,
    ensure_resource_folders,
    standard_output_filename,
)
