import geopy.distance
import numpy as np


def norm_distribution_algorithm(lat: float, long: float, iteration: int, max_matching_distance_meters: int):
    stddev = 0.0000
    new_lat, new_long = 0.0, 0.0
    edgeID, lanePosition, laneIndex = None, None, None
    stddev += 0.0002 * iteration  # add ~ 20 meters per iteration
    new_lat, new_long = add_random_norm_coord_offset(lat=lat, long=long, sd=stddev)
    dist_meters = calc_distance(first_lat=new_lat, first_long=new_long, second_lat=lat,
                                second_long=long)
    if dist_meters > max_matching_distance_meters:
        raise RuntimeError(
            f"ERROR: Could not find edge for iteration {iteration} closer than {max_matching_distance_meters}m to center coord({lat},{long})")
    return new_lat, new_long, dist_meters


NUM_OF_PARTITIONS = 8  # N,NE,E,SE,S,SW,W,NW


def equidistant_circles_algorithm(lat: float, long: float, iteration: int,
                                  max_matching_distance_meters: int):
    radius = 10  # Start with 10 meters search radius
    partition = 0  # N
    found_coord_lat, found_coord_long = None, None
    radius = radius * 2 * int(iteration / NUM_OF_PARTITIONS)  # Double radius every NUM_OF_PARTITIONS (e.g. 8 times)
    partition = iteration % NUM_OF_PARTITIONS
    if radius > max_matching_distance_meters:
        raise RuntimeError(
            f"ERROR: Could not find edge for iteration {iteration} closer than {max_matching_distance_meters}m to center coord({lat},{long})")
    circle_coord_lat, circle_coord_long = circle_around_coordinate(center_lat=lat, center_long=long,
                                                                   radius_m=radius,
                                                                   partitions=NUM_OF_PARTITIONS,
                                                                   curr_partition=partition)
    return circle_coord_lat, circle_coord_long, radius


def add_random_norm_coord_offset(lat: float, long: float, sd: float):
    return lat + np.random.normal(loc=0.0, scale=sd), long + np.random.normal(loc=0.0, scale=sd)


def circle_around_coordinate(center_lat: float, center_long: float, radius_m: int, partitions: int,
                             curr_partition: int):
    point = geopy.distance.distance(kilometers=radius_m / 1000.0).destination((center_lat, center_long),
                                                                              bearing=360.0 / partitions * curr_partition)
    return point.latitude, point.longitude


def calc_distance(first_lat: float, first_long: float, second_lat: float, second_long: float) -> int:
    return int(geopy.distance.geodesic((first_lat, first_long), (second_lat, second_long)).meters)
