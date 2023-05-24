from .sector import Sector
from .coordinates import Coordinates
from math import sqrt
from Tools.logger import elog

class SectorCoordinates:
    def __init__(self):
        self.__sector_coordinates = []
        self.__overall_bbox = {"left": 180, "bottom": 90, "right": -180, "top": -90}

    def __validate_bbox(self, bbox: tuple):
        if len(bbox) != 4:
            raise ValueError(f"bbox {bbox} must contain 4 elements (left, bottom, right, top)")
        left, bottom, right, top = bbox
        if left > right or bottom > top:
            raise ValueError(f"bbox {bbox} must be in the form (left, bottom, right, top)")
        for element in bbox:
            if not isinstance(element, float):
                raise ValueError(f"bbox {bbox} must contain only float elements (geo coordinates)")
    def __update_overall_bbox(self, bbox: tuple):
        left, bottom, right, top = bbox
        if left < self.__overall_bbox["left"]:
            self.__overall_bbox["left"] = left
        if bottom < self.__overall_bbox["bottom"]:
            self.__overall_bbox["bottom"] = bottom
        if right > self.__overall_bbox["right"]:
            self.__overall_bbox["right"] = right
        if top > self.__overall_bbox["top"]:
            self.__overall_bbox["top"] = top

    def __check_duplicates(self, sector: Sector, bbox: tuple, representative_edge: str):
        for sector_coord in self.__sector_coordinates:
            if sector_coord["sector"] == sector:
                raise ValueError(f"sector {sector} already in sector_coordiantes, "
                                 f"len={len(self.__sector_coordinates)}")
            if sector_coord["bbox"] == bbox:
                raise ValueError(f"bbox {bbox} already in sector_coordiantes, "
                                 f"len={len(self.__sector_coordinates)}")
            if sector_coord["representative_edge"] == representative_edge:
                raise ValueError(f"representative_edge {representative_edge} already in sector_coordiantes, "
                                 f"len={len(self.__sector_coordinates)}")
    def add_sector_coordinates(self, sector: Sector, bbox: tuple, representative_edge: str):
        # check if bbox contains 4 elements and if all elements are of type float, and match format
        self.__validate_bbox(bbox)
        # update overall bbox
        self.__update_overall_bbox(bbox)
        # check duplicates (sector, bbox or representative_edge must be unique)
        self.__check_duplicates(sector, bbox, representative_edge)
        self.__sector_coordinates.append({"sector": sector, "bbox": bbox, "representative_edge": representative_edge})

    def representative_edge(self, sector: Sector):
        for sector_coord in self.__sector_coordinates:
            if sector_coord["sector"] == sector:
                return sector_coord["representative_edge"]
        raise ValueError(f"sector {sector} not found in sector_coordiantes, len={len(self.__sector_coordinates)}")

    from math import sqrt

    def find_closest_sector(self, coords: Coordinates) -> Sector:
        closest_sector = None
        min_distance = float('inf')
        for sector_coord in self.__sector_coordinates:
            sector_bbox = sector_coord["bbox"]
            if coords.lon() < sector_bbox[0] or coords.lon() > sector_bbox[2] or \
                    coords.lat() < sector_bbox[1] or coords.lat() > sector_bbox[3]:
                # Coordinates are outside the sector's bbox
                sector_center_lon = (sector_bbox[0] + sector_bbox[2]) / 2
                sector_center_lat = (sector_bbox[1] + sector_bbox[3]) / 2
                distance = sqrt((coords.lon() - sector_center_lon) ** 2 + (coords.lat() - sector_center_lat) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    closest_sector = sector_coord["sector"]
        if closest_sector is None:
            raise ValueError(f"No sector found near the given coordinates: {coords}")
        else:
            elog("Warning: The given coordinates are outside the defined sectors. Closest sector will be used.")
            return closest_sector

    def get_sector(self, coords: Coordinates) -> Sector:
        for sector_coord in self.__sector_coordinates:
            if sector_coord["bbox"][0] <= coords.lon() <= sector_coord["bbox"][2] and \
                    sector_coord["bbox"][1] <= coords.lat() <= sector_coord["bbox"][3]:
                return sector_coord["sector"]
        return self.find_closest_sector(coords)

    def get_sectors_shape(self) -> tuple:
        min_row, max_row, min_col, max_col = (None, None, None, None)
        if len(self.__sector_coordinates) == 0:
            return (0, 0)
        for sector_coord in self.__sector_coordinates:
            if min_row is None or sector_coord["sector"].row() < min_row:
                min_row = sector_coord["sector"].row()
            if max_row is None or sector_coord["sector"].row() > max_row:
                max_row = sector_coord["sector"].row()
            if min_col is None or sector_coord["sector"].col() < min_col:
                min_col = sector_coord["sector"].col()
            if max_col is None or sector_coord["sector"].col() > max_col:
                max_col = sector_coord["sector"].col()
        return (max_row - min_row + 1, max_col - min_col + 1)


