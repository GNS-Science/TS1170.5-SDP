import os
import pathlib

RESOURCES_FOLDER = pathlib.Path(
    pathlib.PurePath(os.path.realpath(__file__)).parent.parent, "resources"
)
