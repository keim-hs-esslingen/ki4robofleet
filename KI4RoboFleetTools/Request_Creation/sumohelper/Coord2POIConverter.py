# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: November 2020
# License: MIT License
# =============================================================================
# This Script uses OsmApi to converts Points of Interest (POIs) from
# Open Street Map (OSM) GeoCoordinates to Edge IDs and Edge Positions which can
# be used by SUMO as Start- or Targetpoints.
# =============================================================================

import time
import numpy as np
import requests
from datetime import datetime, timedelta
from .CoordModification import norm_distribution_algorithm, equidistant_circles_algorithm
import logging

OSM_POI_TAGS_ORDERED = ["amenity", "shop", "leisure", "tourism", "natural", "office", "building"]
DEFAULT_OSM_POI_TAG = "building.apartments"


class OsmInfoObject:
    def __init__(self, osm_id: int, osm_type: str, addr_house_nbr: str, addr_street: str, addr_postcode: str,
                 addr_city: str, addr_country: str):
        self.osm_id = osm_id
        self.osm_type = osm_type
        self.addr_house_nbr = addr_house_nbr
        self.addr_street = addr_street
        self.addr_postcode = addr_postcode
        self.addr_city = addr_city
        self.addr_country = addr_country

    def __str__(self):
        return f"OsmInfoObject: osm_id: {self.osm_id}, osm_type: {self.osm_type}, address: {self.address()}"

    def id(self) -> int:
        return self.osm_id

    def is_type_relation(self) -> bool:
        return self.osm_type == "relation"

    def address(self) -> (str, str, str, str):
        return f"{self.addr_house_nbr} {self.addr_street}", self.addr_postcode, self.addr_city, self.addr_country


def findBestFittingPoi(lat: float, long: float, corr_algorithm: str = "eqdistcircles",
                       max_matching_distance_meters: int = 500, total_timeout: int = 60) -> (str, int):
    start_time = datetime.now()
    iteration = 0
    new_lat, new_long, dist_meters = lat, long, 0

    while True:
        if datetime.now() > start_time + timedelta(seconds=total_timeout):
            raise TimeoutError(f"Could not find POI tag for ({lat},{long})s")
        try:
            return request_poi(lat=new_lat, long=new_long)
        except TimeoutError as t_e:
            continue
        except LookupError as lu_e:
            iteration += 2
            if corr_algorithm == "normdist":
                new_lat, new_long, dist_meters = norm_distribution_algorithm(lat=lat, long=long, iteration=iteration,
                                                                             max_matching_distance_meters=max_matching_distance_meters)
            elif corr_algorithm == "eqdistcircles":
                new_lat, new_long, dist_meters = equidistant_circles_algorithm(lat=lat, long=long, iteration=iteration,
                                                                               max_matching_distance_meters=max_matching_distance_meters)
            else:
                raise RuntimeError(f"ERROR: Unknown 'corr_algorithm': '{corr_algorithm}'")


def get_default_poi() -> str:
    return DEFAULT_OSM_POI_TAG


def request_poi(lat: float, long: float, timeout: int = 20) -> (str, int):
    start_time = datetime.now()
    poi_tag = None
    while True:
        if datetime.now() > start_time + timedelta(seconds=timeout):
            raise TimeoutError(f"Could not find matching tag in {timeout}s")
        try:
            osm_info_obj = nominatim_reverse_get_osminfoobj(lat=lat, long=long)
        except RuntimeError as re:
            logging.warning(re)
            continue
        except LookupError as le:
            logging.debug(le)
            raise LookupError(le)
        except Exception as e:
            logging.error(e)
            continue
        if osm_info_obj.is_type_relation():
            logging.debug(f"Found relation: {str(osm_info_obj)}")
            try:
                poi_tag = nominatim_details_get_poi_tag(osm_id=osm_info_obj.id())
                break
            except RuntimeError as re:
                logging.warning(re)
                continue
            except Exception as e:
                logging.error(e)
                continue
        else:
            logging.debug(f"Trying to find POI tag by address: {str(osm_info_obj)}")
            try:
                poi_tag = nominatim_search_get_poi_tag(osm_info_obj=osm_info_obj)
                break
            except RuntimeError as re:
                logging.warning(re)
                continue
            except LookupError as le:
                logging.warning(le)
                raise LookupError(le)
            except Exception as e:
                logging.error(e)
                continue
    start_time = datetime.now()
    way_id = None
    iteration = 0
    new_lat, new_long = lat, long
    while True:
        # mit new_lat und new_long so lange Anfragen an reverse schicken bis osm_type == way ist
        if datetime.now() > start_time + timedelta(seconds=timeout):
            raise TimeoutError(f"Could not find POI tag for ({lat},{long})s")
        try:
            way_id = nominatim_reverse_get_wayid(lat=new_lat, long=new_long)
            break
        except TimeoutError as t_e:
            continue
        except LookupError as lu_e:
            iteration += 1
            new_lat, new_long, dist_meters = norm_distribution_algorithm(lat=lat, long=long, iteration=iteration, max_matching_distance_meters=500)
    return poi_tag, way_id


def nominatim_reverse_get_osminfoobj(lat: float, long: float) -> OsmInfoObject:
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/reverse?lat={lat:.8f}&lon={long:.8f}&format=json&addressdetails=1&extratags=0")
    except requests.HTTPError as http_err:
        raise RuntimeError(f'HTTP error occurred: {http_err}')
    except Exception as err:
        raise RuntimeError(f'Other error occurred: {err}')
    if response.status_code == 200:
        content = response.json()
        addr = content["address"]
        for tag in OSM_POI_TAGS_ORDERED:
            if tag in addr:  # e.g. "amenity"
                if "house_number" in addr:
                    return OsmInfoObject(content["osm_id"], content["osm_type"], addr['house_number'], addr['road'],
                                         addr["postcode"], addr["city"], addr["country"])
                else:
                    return OsmInfoObject(content["osm_id"], content["osm_type"], "-1", addr['road'],
                                         addr["postcode"], addr["city"], addr["country"])
        raise LookupError(f"Nominatim Reverse by Coord: Could not find a matching POI tag for ({lat},{long})")
    elif response.status_code == 429:
        time.sleep(2)
    else:
        raise RuntimeError(f"Status Code: {response.status_code}")


def nominatim_reverse_get_wayid(lat: float, long: float) -> int:
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/reverse?lat={lat:.8f}&lon={long:.8f}&format=json&addressdetails=0&extratags=0")
    except requests.HTTPError as http_err:
        raise RuntimeError(f'HTTP error occurred: {http_err}')
    except Exception as err:
        raise RuntimeError(f'Other error occurred: {err}')
    if response.status_code == 200:
        content = response.json()
        if content["osm_type"] == "way":
            return content["osm_id"] #  osm_id as way id. Use https://www.openstreetmap.org/way/2329832716 for testing
        else:
            raise LookupError(f"Nominatim Reverse by Coord: Could not find a matching POI tag for ({lat},{long})")
    elif response.status_code == 429:
        time.sleep(2)
    else:
        raise RuntimeError(f"Status Code: {response.status_code}")

# returns e.g. "amenity.place_of_worship", docs: https://wiki.openstreetmap.org/wiki/Map_features
def nominatim_details_get_poi_tag(osm_id: int) -> str:
    osm_type = "R"
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/details?osmtype={osm_type}&osmid={osm_id}&format=json")
    except requests.HTTPError as http_err:
        raise RuntimeError(f'HTTP error occurred: {http_err}')
    except Exception as err:
        raise RuntimeError(f'Other error occurred: {err}')
    if response.status_code == 200:
        content = response.json()
        return f"{content['category']}.{content['type']}"  # e.g. "amenity.place_of_worship"
    elif response.status_code == 429:
        time.sleep(2)
    else:
        raise RuntimeError(f"Status Code: {response.status_code}")


def nominatim_search_get_poi_tag(osm_info_obj: OsmInfoObject) -> str:
    street, postalcode, city, country = osm_info_obj.address()
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/search?street={street}&postalcode={postalcode}&city={city}&country={country}&format=json")
    except requests.HTTPError as http_err:
        raise RuntimeError(f'HTTP error occurred: {http_err}')
    except Exception as err:
        raise RuntimeError(f'Other error occurred: {err}')
    if response.status_code == 200:
        arr = response.json()
        for tag in OSM_POI_TAGS_ORDERED:
            for obj in arr:
                if tag == obj['class']:  # e.g. "amenity"
                    return f"{obj['class']}.{obj['type']}"  # e.g. "amenity.place_of_worship"
        raise LookupError(f"Nominatim Search (by address): Could not find a matching POI tag for '{str(osm_info_obj)}'")
    elif response.status_code == 429:
        time.sleep(2)
    else:
        raise RuntimeError(f"Status Code: {response.status_code}")


# Example for response from OSM nominatim API. Docs: https://nominatim.org/release-docs/latest/api/Reverse/#parameters
"""
{
    "place_id": 21359405,
    "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
    "osm_type": "node",
    "osm_id": 2356829152,
    "lat": "47.6237946",
    "lon": "-122.3568472",
    "display_name": "Blue Water Taco Grill, 515, Queen Anne Avenue North, Uptown, Belltown, Seattle, King County, Washington, 98109, United States",
    "address": {
        "amenity": "Blue Water Taco Grill",
        "house_number": "515",
        "road": "Queen Anne Avenue North",
        "neighbourhood": "Uptown",
        "suburb": "Belltown",
        "city": "Seattle",
        "county": "King County",
        "state": "Washington",
        "ISO3166-2-lvl4": "US-WA",
        "postcode": "98109",
        "country": "United States",
        "country_code": "us"
    },
    "boundingbox": [
        "47.6237446",
        "47.6238446",
        "-122.3568972",
        "-122.3567972"
    ]
}
"""
