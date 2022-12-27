from .edge_coordinates import EdgeCoordinates
from .coordinates import Coordinates
from .sector_coordinates import SectorCoordinates
from .sector import Sector


class EdgeSectorConverter:
    def __init__(self, edge_coords: EdgeCoordinates, sector_coords: SectorCoordinates):
        self.__edge_coords = edge_coords
        self.__sector_coords = sector_coords

    def __get_coords_by_edge(self, edge_id: str) -> Coordinates:
        return self.__edge_coords.get_coord(edge_id)

    def __get_sector_by_coords(self, coords: Coordinates) -> Sector:
        return self.__sector_coords.get_sector(coords)

    # returns the sector that contains the edge
    def to_sector(self, edge_id: str) -> Sector:
        coords = self.__get_coords_by_edge(edge_id)
        return self.__get_sector_by_coords(coords)

    # returns a edge, that represents the sector
    def to_edge(self, sector: Sector) -> str:
        return self.__sector_coords.representative_edge(sector)
