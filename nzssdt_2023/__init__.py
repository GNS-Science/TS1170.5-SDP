import os
import pathlib

__version__ = '0.1.0'

RESOURCES_FOLDER = pathlib.Path(
    pathlib.PurePath(os.path.realpath(__file__)).parent.parent, "resources"
)
