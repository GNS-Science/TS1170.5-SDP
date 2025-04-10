#! python3
"""
Configuration module for the library.

NB: most users will never need this. It's mainly  for NSHM developers.
"""
import os
import tempfile
from pathlib import PurePath

RESOURCES_FOLDER = str(PurePath(os.path.realpath(__file__)).parent.parent / "resources")
REPORTS_FOLDER = str(PurePath(os.path.realpath(__file__)).parent.parent / "reports")
DELIVERABLES_FOLDER = str(PurePath(os.path.realpath(__file__)).parent.parent / "deliverables")

WORKING_FOLDER = os.getenv("WORKING_FOLDER", tempfile.gettempdir())
"""A standardised directory path for disposable working files."""

DISAGG_HAZARD_ID = "NSHM_v1.0.4_mag"
"""Disaggregations for calculation of mean magnitude were done for magnitude only (rather than mag,
dist, TRT, and epsilon) for computational speed and are stored with a unique hazard ID."""
