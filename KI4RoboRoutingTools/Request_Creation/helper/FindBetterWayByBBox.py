import sys
import re

# regex-Muster um bbox aus der Eingabezeichenfolge zu extrahieren
bbox_pattern = re.compile(r"bbox=\[(\S+),\s(\S+),\s(\S+),\s(\S+)\]")

# Funktion zum Berechnen des Mittelpunkts aus den bbox-Koordinaten
def calculate_center(bbox):
    left, bottom, right, top = map(float, bbox)
    center_lat = (top + bottom) / 2
    center_lon = (left + right) / 2
    return center_lat, center_lon

# Eingabeparameter auslesen und bbox extrahieren
args = sys.argv[1:]
bbox = None
for arg in args:
    match = bbox_pattern.match(arg)
    if match:
        bbox = match.groups()
        break

# Fehlermeldung, falls keine bbox gefunden wurde
if not bbox:
    print("Fehler: Keine bbox gefunden.")
    sys.exit()

# Mittelpunkt berechnen
center_lat, center_lon = calculate_center(bbox)

# OpenStreetMap-Link generieren und ausgeben
osm_link = f"https://www.openstreetmap.org/#map=16/{center_lat}/{center_lon}"
print(osm_link)
