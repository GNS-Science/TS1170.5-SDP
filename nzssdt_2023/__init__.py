import os
import pathlib

__version__ = '0.2.0'

RESOURCES_FOLDER = pathlib.Path(
    pathlib.PurePath(os.path.realpath(__file__)).parent.parent, "resources"
)
