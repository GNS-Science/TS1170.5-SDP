"""
This module contains end user functions for spatially identifying the relevant TS row and distance calculations
"""

import geopandas as gpd
import numpy as np
from shapely.geometry import Point

from nzssdt_2023.end_user_functions.constants import FAULTS, GRID_PTS, NZ_MAP, POLYGONS


def identify_location_id(longitude: float, latitude: float) -> str:
    """Identifies the TS location assigned to a latitute and longitude

    Args:
        longitude: longitude of the point of interest
        latitude: latitude of the point of interest

    Returns:
        location_id: name of the relevant TS location
    """

    # check whether point falls within New Zealand
    if sum(NZ_MAP.contains(Point(longitude, latitude))) > 0:

        # identify polygons that the point falls within
        point_location = Point(longitude, latitude)
        within_idx = POLYGONS.contains(point_location)

        # if point falls in a polygon
        if sum(within_idx) > 0:
            # confirm that it only falls in one polygon
            assert sum(within_idx) == 1, "Point falls within more than one polygon"
            location_id = POLYGONS[within_idx].index[0]

        # if point does not fall in a polygon
        else:
            # calculate distance to all grid points
            grid_dist = GRID_PTS.geometry.apply(
                lambda x: point_location.distance(x)
            ).round(4)
            # find the closest locations (ordered by northwest, NE, SW, SE)
            closest_idx = np.where(grid_dist == grid_dist.min())[0]
            # for equidistant points, take the first
            location_id = GRID_PTS.index[closest_idx[0]]

    else:
        location_id = "outside NZ"

    return location_id


def calculate_distance_to_fault(longitude: float, latitude: float) -> float:
    """Calculates the distance from a latitude and longitude point to the nearest fault

    Args:
        longitude: longitude of the point of interest
        latitude: latitude of the point of interest

    Returns:
        d: distance to fault, rounded to nearest kilometre
    """
    point_location = Point(longitude, latitude)
    latlon = gpd.GeoDataFrame(geometry=[point_location], crs="EPSG:4326")

    # convert to NZTM for distance calcs
    latlon_nztm = latlon.to_crs(epsg=2193)
    faults_nztm = FAULTS.to_crs(epsg=2193)

    # calculate minimum distance to fault
    d = round(
        latlon_nztm.geometry.apply(lambda x: faults_nztm.distance(x).min()) / 1000.0
    )

    return d[0]
