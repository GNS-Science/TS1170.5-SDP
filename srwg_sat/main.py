#!python main.py

import os
import pathlib
import pandas as pd


RESOURCES_FOLDER = pathlib.Path(pathlib.PurePath(os.path.realpath(__file__)).parent.parent, 'resources')


filename = 'SaT-variables_v5_corrected-locations.pkl'

df = pd.read_pickle(pathlib.Path(RESOURCES_FOLDER, filename))

print(df.info())

APoEs = [f'APoE: 1/{rp}' for rp in [25,100,250,500,1000,2500]]
site_class_labels = [f'Site Soil Class {n}' for n in ['I','II','III','IV','V','VI']]
parameters = ['PGA','Sas','Tc']




# easy way to split the df into the two tables
sites = list(df.index)
named_sites = [site for site in sites if '~' not in site]
grid_sites  = [site for site in sites if '~' in site]

print('named_sites')
print(df.loc[named_sites,:])

print('grid_sites')
print(df.loc[grid_sites,:])