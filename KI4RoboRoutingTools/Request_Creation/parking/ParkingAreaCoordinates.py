import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
import requests


class ParkingAreaCoordinates:
    def __init__(self, xml_file: str):
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        self.way_ids = [elem.get('id') for elem in self.root.findall('./parkingArea')]

    def remove_parking_area(self, way_id: str) -> bool:
        parking_area_node = self.root.find(f"./parkingArea[@id='{way_id}']")
        if parking_area_node is not None:
            self.root.remove(parking_area_node)
            return True
        return False
    def additional_edge_coords(self) -> List[Dict[str, str]]:
        coords = []
        for way_id in self.way_ids:
            try:
                lat, lon = self.get_way_coordinates(way_id)
                coords.append({"edge_id": way_id, "lat": lat, "lon": lon})
            except RuntimeError as e:
                print(e)
        return coords

    def get_way_coordinates(self, way: str) -> Tuple[float, float]:
        # Nominatim API-Endpunkt
        url = "https://nominatim.openstreetmap.org/lookup"
        # Anfrageparameter
        params = {"osm_ids": "W{}".format(way), "format": "json"}
        # Anfrage an die API senden
        response = requests.get(url, params=params)
        # JSON-Response verarbeiten
        data = response.json()
        # Überprüfen, ob Koordinaten vorhanden sind
        if len(data) == 0 or 'lat' not in data[0] or 'lon' not in data[0]:
            # Wenn keine Koordinaten gefunden wurden, eine RuntimeError-Exception mit einer Beschreibung werfen
            self.remove_parking_area(way_id=way)
            raise RuntimeError(f"Keine Koordinaten gefunden für den Way {way}. Removed it from xml")
        # Koordinaten zurückgeben
        return float(data[0]['lat']), float(data[0]['lon'])
