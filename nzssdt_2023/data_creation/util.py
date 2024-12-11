"""
utility functions
"""
import pandas as pd
from nzshm_common.location import CodedLocation


def set_coded_location_resolution(dataframe_with_location: pd.DataFrame):
    """Sets the dataframe index to coded_locations with res 0.1"""

    def replace_coded_location(loc):
        """user function (ufunc) to update coded location values"""
        if "~" not in loc:
            return loc
        lat, lon = map(float, loc.split("~"))
        return CodedLocation(lat, lon, resolution=0.1).code

    loc_series = dataframe_with_location.index.to_series().apply(replace_coded_location)

    return dataframe_with_location.set_index(loc_series)
