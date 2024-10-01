"""
This convert package provides classes to handle dataframe structures from the original data produce by AnneH.


TODO:
 - potentially unify the data structures across 'convert' , 'data_creation` and 'publish' packages.
 - look for duplication in constants as above.

Modules:
    dist_mag_table: a class for D&M dataframes
    sat_table: a class for  SA dataframes
"""
from .dist_mag_table import DistMagTable
from .sat_table import SatTable
