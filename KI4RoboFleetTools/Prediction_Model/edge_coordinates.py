from .coordinates import Coordinates


class EdgeCoordinates:
    def __init__(self):
        self.__edge_cooridnates = []

    def __check_duplicates(self, edge_id: str):
        for edge_coord in self.__edge_cooridnates:
            if edge_coord["edge_id"] == edge_id:
                raise ValueError(f"edge_id {edge_id} already exists in edge_coord_list(len={len(self.__edge_cooridnates)})")

    def add_edge_coordinates(self, edge_id: str, coords: Coordinates):
        # check if edge_id already exists, coord duplicates are allowed
        self.__check_duplicates(edge_id)
        self.__edge_cooridnates.append({"edge_id": edge_id, "coords": coords})

    def get_coord(self, edge_id: str):
        for edge_coord in self.__edge_cooridnates:
            if edge_coord["edge_id"] == edge_id:
                return edge_coord["coords"]
        raise ValueError(f"edge_id {edge_id} not found in edge_coord_list(len={len(self.__edge_cooridnates)})")