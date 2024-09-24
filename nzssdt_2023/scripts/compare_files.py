import pickle as pkl
import pandas as pd
import numpy as np

# check the pkl files

filename = "original_files/SaT-variables_v5_corrected-locations.pkl"
with open(filename, "rb") as file:
    original_df = pkl.load(file)

filename = "recreated_SaT-variables.pkl"
with open(filename, "rb") as file:
    recreated_df = pkl.load(file)

if np.all(np.isclose(original_df.to_numpy(), recreated_df.to_numpy())):
    print("All Sa parameter values in the .pkl files are equivalent.")
else:
    print("Some Sa parameter values in the .pkl files are different.")


# check the csv files

filename = "original_files/D_and_M_with_floor.csv"
original_df = pd.read_csv(filename)

filename = "recreated_D-M-tables.csv"
recreated_df = pd.read_csv(filename)

if original_df.equals(recreated_df):
    print("All D and M values in the .csv files are the same.")
else:
    print("Some D and M values in the .csv files are not the same.")
