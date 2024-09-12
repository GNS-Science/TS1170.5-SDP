import os
import pathlib


__version__ = "0.4.0"

from .data_creation.query_NSHM import *

RESOURCES_FOLDER = pathlib.Path(
    pathlib.PurePath(os.path.realpath(__file__)).parent.parent, "resources"
)
