"""
This module contains functions spatially identifying the relevant TS row and distance calculations
"""

import numpy as np
import geopandas as gpd
from shapely.geometry import Point

from end_user_functions.constants import (
    POLYGONS,
    FAULTS,
    GRID_PTS
)

def identify_location_id(longitude, latitude):
    """ Identifies the TS location assigned to a latitute and longitude

    Args:
        longitude: longitude of the point of interest
        latitude: latitude of the point of interest

    Returns:
        location_id: name of the relevant TS location
    """
    # identify polygons that the point falls within
    point_location = Point(longitude, latitude)
    within_idx = POLYGONS.contains(point_location)

    # if point falls in a polygon
    if sum(within_idx) > 0:
        # confirm that it only falls in one polygon
        assert sum(within_idx) == 1, 'Point falls within more than one polygon'
        location_id = POLYGONS[within_idx].index[0]

    # if point does not fall in a polygon
    else:
        # calculate distance to all grid points
        grid_dist = GRID_PTS.geometry.apply(lambda x: point_location.distance(x)).round(4)
        # find the closest locations (ordered by northwest, NE, SW, SE)
        closest_idx = np.where(grid_dist == grid_dist.min())[0]
        # for equidistant points, take the first
        location_id = GRID_PTS.index[closest_idx[0]]

    return location_id


def calculate_distance_to_point(longitude, latitude, round_down=False):
    """ Calculates the distance from a point to the nearest fault

    Args:
        longitude: longitude of the point of interest
        latitude: latitude of the point of interest
        round_down: true rounding to nearest integer (default) or to lower integer

    Returns:
        d: distance to fault, reported to nearest kilometre
    """
    point_location = Point(longitude, latitude)
    latlon = gpd.GeoDataFrame(geometry=[point_location], crs='EPSG:4326')

    # convert to NZTM for distance calcs
    latlon_nztm = latlon.to_crs(epsg=2193)
    faults_nztm = FAULTS.to_crs(epsg=2193)

    # calculate minimum distance to fault
    d = latlon_nztm.geometry.apply(lambda x: faults_nztm.distance(x).min()) / 1000.

    # round down to lower integer (NOT DEFAULT BEHAVIOR)
    if round_down:
        d = np.floor(d[0])
    else:
        d = np.round(d[0])

    return d