#! python3
"""
Configuration module for the library.

NB: most users will never need this. It's mainly  for NSHM developers.
"""
import os
from pathlib import PurePath

RESOURCES_FOLDER = str(PurePath(os.path.realpath(__file__)).parent.parent / "resources")

WORKING_FOLDER = os.getenv('WORKING_FOLDER', "/tmp")
"""A standardised directory path for disposable working files."""

