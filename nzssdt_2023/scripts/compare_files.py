"""
From Annes jupyter comparison
"""
import pickle as pkl

import numpy as np
import pandas as pd
import pathlib

# check the pkl files
from nzssdt_2023.config import RESOURCES_FOLDER, WORKING_FOLDER

filename = (
    pathlib.Path(RESOURCES_FOLDER)
    / "pipeline/v1/SaT-variables_v5_corrected-locations.pkl"
)
with open(filename, "rb") as file:
    original_df = pkl.load(file)

filename = pathlib.Path(WORKING_FOLDER) / "recreated_SaT-variables.pkl"
with open(filename, "rb") as file:
    recreated_df = pkl.load(file)

if np.all(np.isclose(original_df.to_numpy(), recreated_df.to_numpy())):
    print("All Sa parameter values in the .pkl files are equivalent.")
else:
    print("Some Sa parameter values in the .pkl files are different.")


# check the csv files

filename = pathlib.Path(RESOURCES_FOLDER) / "pipeline/v1/D_and_M_with_floor.csv"
original_df = pd.read_csv(filename)

filename = pathlib.Path(WORKING_FOLDER) / "recreated_D-M-tables.csv"
recreated_df = pd.read_csv(filename)

if original_df.equals(recreated_df):
    print("All D and M values in the .csv files are the same.")
else:
    print("Some D and M values in the .csv files are not the same.")
