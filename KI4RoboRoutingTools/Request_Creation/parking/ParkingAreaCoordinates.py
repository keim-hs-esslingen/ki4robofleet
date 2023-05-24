import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
import requests
import time


class ParkingAreaCoordinates:
    def __init__(self, xml_file: str):
        self.xml_file = xml_file
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        self.parkingAreas = [{"id": elem.get('id'), "way": elem.get('lane')} for elem in self.root.findall('./parkingArea')]

    def additional_edge_coords(self) -> List[Dict[str, str]]:
        coords = []
        for parkingArea in self.parkingAreas:
            try:
                lat, lon = self.get_way_coordinates(parkingArea['id'])
                coords.append({"edge_id": parkingArea['way'], "lat": lat, "lon": lon})
            except RuntimeError as e:
                print(e)
                self.remove_parking_area(parkingArea['id'])
        self.tree.write(self.xml_file)
        return coords

    def get_way_coordinates(self, parkingArea_id: str) -> Tuple[float, float]:
        # Nominatim API-Endpunkt
        url = "https://nominatim.openstreetmap.org/lookup"
        # Anfrageparameter
        params = {"osm_ids": "W{}".format(parkingArea_id), "format": "json"}
        # Anfrage an die API senden
        for i in range(10):
            response = requests.get(url, params=params)
            if response.status_code != 200:
                time.sleep(1.0)
                continue
            data = response.json()
            # Überprüfen, ob Koordinaten vorhanden sind
            if len(data) == 0 or 'lat' not in data[0] or 'lon' not in data[0]:
                # Wenn keine Koordinaten gefunden wurden, eine RuntimeError-Exception mit einer Beschreibung werfen
                raise RuntimeError("Keine Koordinaten gefunden für den Way {}".format(parkingArea_id))
            # Koordinaten zurückgeben
            return float(data[0]['lat']), float(data[0]['lon'])
        raise RuntimeError("Network issue".format(parkingArea_id))



    def remove_parking_area(self, parkingArea_id: str):
        for elem in self.root.findall('./parkingArea'):
            if elem.get('id') == parkingArea_id:
                self.root.remove(elem)
                break
