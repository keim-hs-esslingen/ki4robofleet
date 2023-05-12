#!.\venv\Scripts\python.exe
import logging
import pandas as pd
import sys, os
from datetime import datetime
from sklearn.model_selection import train_test_split

from sumohelper.NetFilter import EdgeFilter
from sumohelper.Coord2EdgeConverter import EdgeFinder
from sumohelper.Coord2POIConverter import findBestFittingPoi, get_default_poi
from sumohelper.CustomerRequestAccess import CustomerRequestAccess, CustomerRequest
from sumohelper.PoiEdgesAccess import PoiEdgesAccess, PoiEdge
from sumohelper.EdgeCoordsAccess import EdgeCoordsAccess, EdgeCoord
from sumohelper.SectorCoordsAccess import SectorCoordsAccess, SectorCoord
from helper.TimeHelperFunction import timediff_seconds, to_car2go_format
from helper.RequestFilter import filter_by_datettime
from helper.NycFormatConversionAndFilter import convert_nyc_to_sumo4av_format, filter_by_lat_long
from dataseteval import MapMetrics, MapPlotter, DateTimeHelper
from sectorizing import Sectorizing
from parking import ParkingAreaCoordinates


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(filename=f'Request_Creation_{datetime.now().isoformat()}', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def build_output_path(city: str, filename: str):
    basepath = os.path.dirname(os.path.abspath(__file__)) + f"/_output/{city}_{datetime.now().strftime('%Y-%m-%d')}/"
    if not os.path.exists(basepath):
        os.makedirs(basepath)
    return basepath + filename

# input format of the csv
#|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|
#|       | LOCATIONID | VEHICLE_VIN       | STARTED_LOCAL       | DURATION | DISTANCE | STARTLAT         | STARTLONG         | FINISHLAT        | FINISHLONG        |
#|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|
#|     1 |         21 | WMEEJ3BA1CK569248 | 2014-10-10 08:17:43 |      572 |        2 |  47.605677717487 |  -122.31457969117 |  47.598724628692 |  -122.32936565843 |
#|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|
#|     2 |         21 | WMEEJ3BA2DK655962 | 2014-10-10 08:59:37 |      775 |        4 | 47.6384753901182 | -122.319772520717 |  47.612720772532 |  -122.34152449399 |
#|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|
#|     4 |         21 | WMEEJ3BA1DK683381 | 2014-10-10 08:59:54 |     1359 |        5 | 47.6622810152178 | -122.314231978052 |  47.625007918311 |  -122.33499524964 |
#|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|
#|     6 |         21 | WMEEJ3BA8DK655321 | 2014-10-10 06:53:27 |      439 |        3 | 47.6928912709091 | -122.306901580199 |  47.709615453682 |  -122.31787668988 |
#|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|
#|     7 |         21 | WMEEJ3BA5CK575165 | 2014-10-10 07:43:58 |      828 |        4 |  47.648829314253 |  -122.34772824806 |  47.623967283971 |  -122.33265563173 |
#|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|
#|    10 |         21 | WMEEJ3BA1CK573655 | 2014-10-10 07:44:25 |      281 |        1 | 47.6547255606243 | -122.373674595368 | 47.6629051839964 | -122.369596853198 |

STEP_SIZE_SECTORS = 5000

KEY_WEEKDAY = 'WEEKDAY'
KEY_HOUR = 'HOUR'
KEY_STARTLAT = 'STARTLAT'
KEY_STARTLONG = 'STARTLONG'
KEY_FINLAT = 'FINISHLAT'
KEY_FINLONG = 'FINISHLONG'

COLUMNS = ['idx', 'start_lat', 'start_long',
           'start_edge', 'start_edge_pos', 'start_poi', 'start_poi_way_id', 'finish_lat', 'finish_long',
           'finish_edge', 'finish_edge_pos', 'finish_poi', 'finish_poi_way_id']
COLUMNS_LATLONG_EDGES = ["edge_id", "lat", "long"]

SIMU_START_DATETIME = datetime(year=2016, month=5, day=6, hour=12, minute=0, second=0)
#SIMU_END_DATETIME = datetime(year=2016, month=5, day=6, hour=12, minute=1, second=59)
SIMU_END_DATETIME = datetime(year=2016, month=5, day=6, hour=13, minute=59, second=59)


# 1 Find Edges that are reachable both from pedestrians as well as cars --> List
# 2 STARTLAT, STARTLONG, FINISHLAT, FINISHLONG in Edge übersetzen
# 3 CustomerRequests.xml aus start und finish Edge erstellen + Simuzeit


def main(sumo_working_dir: str, trips: str):
    if len(sumo_working_dir) == 0:
        logging.error("Sumo working dir unknown")
        return -1
    if not os.path.exists(sumo_working_dir):
        logging.error("Sumo working dir path does not exists")
        return -1
    complete_sumo_dir = os.path.abspath(sumo_working_dir)

    if len(trips) == 0:
        logging.error("Trips config file unknown")
        return -1
    if not os.path.exists(trips):
        logging.error("Trips config file path does not exists")
        return -1
    complete_sumo_dir = os.path.abspath(sumo_working_dir)
    complete_trips_file = os.path.abspath(trips)
    # 1. XML- Datei "osm.net.xml" importieren
    # 2. NetFilter nach Edges filtern, mit lanes die eine disallow Funktion haben; Rückgabe: EdgeId
    #  https://sumo.dlr.de/docs/Simulation/VehiclePermissions.html
    edge_filter = EdgeFilter(f"{complete_sumo_dir}/osm.net.xml")
    # this section is a bit confusing
    # lanes usually have the attribute 'allow' or 'disallow'
    # if the attribute 'allow' is defined it is a special lane (e.g. a bicycle lane)
    # if the attribute 'disallow' is defined it is a common lane (e.g. for passenger cars)
    # to position a waiting person we need an edge which contains at least one common lane
    # otherwise errors will occur
    edges_for_cars = edge_filter.filter({"disallow": "NOT_EMPTY"}, distinct=True)
    logging.info(f"### Filtered EdgeIDs ####\n{edges_for_cars}\n########################")
    with open('edges_for_cars.txt', 'w') as f:
        f.writelines(["%s\n" % edge for edge in edges_for_cars])

    # 3. LAT & LONG in EdgeId umwandeln.
    edge_finder = EdgeFinder(f"{complete_sumo_dir}/osm.sumocfg")

    # filter set of trips by simulation start and end time
    trips = filter_by_datettime(df=filter_by_lat_long(convert_nyc_to_sumo4av_format(complete_trips_file),
                                    long_min=-74.02749, lat_min=40.57406, long_max=-73.85266, lat_max=40.71400),
                                from_dt=SIMU_START_DATETIME,
                                to_dt=SIMU_END_DATETIME)

    print(trips.head())

    # Print metrics from filtered trips
    metrics = MapMetrics.process_map_metrics(trips)
    print(metrics)
    try:
        city = metrics['city']
    except:
        city = "Unknown City"
    # Plot data
    MapPlotter.plot_coordinates_with_px(trips, title=f"{city} trips")

    # Enrich with time
    DateTimeHelper.enrich_weekday_and_hour(trips)

    # Enrich with sectors
    rows, cols, step_meters = Sectorizing.sector_hints(
        distance_NS_km=int(metrics['distance_northsouth']),
        distance_EW_km=int(metrics['distance_eastwest']),
        row_count=len(trips),
        hours=(trips['WEEKDAY'].max() - trips['WEEKDAY'].min() + 1) * 24,
        step_meters=STEP_SIZE_SECTORS)
    print(f"Taking {rows} rows & {cols} cols")
    sectorizer = Sectorizing.Sectorizer(df=trips, row_count=rows, col_count=cols, edge_finder=edge_finder)
    trips = sectorizer.enrich_sectors()
    list_sector_coords = sectorizer.bbox_of_sectors()
    additional_edge_coords = sectorizer.additional_edge_coords()
    parking_edge_coords = ParkingAreaCoordinates.ParkingAreaCoordinates(xml_file=f"{complete_sumo_dir}/parkingAreas.xml").additional_edge_coords()
    sector_coords_creator = SectorCoordsAccess()
    for sector_dict in list_sector_coords:
        sector_coords_creator.add_sector_coord(SectorCoord(row=sector_dict['row'],
                                                           col=sector_dict['col'],
                                                           bbox=sector_dict['bbox'],
                                                           representative_edge=sector_dict['representative_edge']))
    sector_coords_creator.dump(build_output_path(city, "SectorCoords.xml"))

    # Perform train test split for later processing
    trips_train, trips_test = train_test_split(trips, test_size=0.1)
    # Plot train and test data
    MapPlotter.plot_coordinates_with_px(trips_train, title=f"{city}  trips (train)")
    MapPlotter.plot_coordinates_with_px(trips_test, title=f"{city}  trips (test)")

    # Aggregate trips to request count per sector and hour
    df_agg_requests_train = Sectorizing.aggregated_requests(trips_train, zero_req_padding=True,
                                                            fix_row_col_count=(rows, cols))
    df_agg_requests_test = Sectorizing.aggregated_requests(trips_test, zero_req_padding=True,
                                                           fix_row_col_count=(rows, cols))

    # Export CSV
    df_agg_requests_train.to_csv(build_output_path(city, f"df_{city}_requests_agg_sectors_{step_meters}m_train.csv"))
    df_agg_requests_test.to_csv(build_output_path(city, f"df_{city}_requests_agg_sectors_{step_meters}m_test.csv"))

    mapped_edges, unmapped_edges, edge_coords = [
        pd.DataFrame(columns=COLUMNS),
        pd.DataFrame(columns=COLUMNS),
        pd.DataFrame(columns=COLUMNS_LATLONG_EDGES)]
    mapped_trips_test = trips_test.copy()
    for idx, trip in trips_test.iterrows():
        trip_info = f"Trip({idx},lat={trip[KEY_STARTLAT]},long={trip[KEY_STARTLONG]})"
        start_coord_valid, finish_coord_valid, start_poi_valid, finish_poi_valid = False, False, False, False
        start_poi, start_way_id, finish_poi, finish_way_id, \
            start_lane_pos, start_lane_idx, finish_lane_pos, finish_lane_idx = "", "", "", "", "", "", "", ""
        try:
            logging.info(f"{trip_info}: Find best fitting 'start edge'...")
            start_edge, start_lane_pos, start_lane_idx = edge_finder.findBestFittingEdge(
                lat=trip[KEY_STARTLAT], long=trip[KEY_STARTLONG],
                edges_list=edges_for_cars, allow_correction=False, corr_algorithm="eqdistcircles",
                max_matching_distance_meters=250)
            start_coord_valid = True
        except RuntimeError as e:
            logging.error(f"{trip_info}:{e}")
            start_edge = "-1"
        try:
            logging.info(f"{trip_info}: Find best fitting 'start POI'...")
            start_poi, start_way_id = findBestFittingPoi(lat=trip[KEY_STARTLAT], long=trip[KEY_STARTLONG], corr_algorithm="normdist",
                                           max_matching_distance_meters=500)
            start_poi_valid = True
        except RuntimeError as re:
            logging.warning(f"{trip_info}:{re}")
            start_poi = get_default_poi()
        try:
            logging.info(f"{trip_info}: Find best fitting 'finish edge'...")
            finish_edge, finish_lane_pos, finish_lane_idx = edge_finder.findBestFittingEdge(
                lat=trip[KEY_FINLAT], long=trip[KEY_FINLONG],
                edges_list=edges_for_cars, allow_correction=False, corr_algorithm="eqdistcircles",
                max_matching_distance_meters=250)
            finish_coord_valid = True
        except RuntimeError as e:
            logging.error(f"{trip_info}:{e}")
            finish_edge = "-1"
        try:
            logging.info(f"{trip_info}: Find best fitting 'start POI'...")
            finish_poi, finish_way_id = findBestFittingPoi(lat=trip[KEY_FINLAT], long=trip[KEY_FINLONG], corr_algorithm="normdist",
                                            max_matching_distance_meters=500)
            finish_poi_valid = True
        except RuntimeError as re:
            logging.warning(f"{trip_info}:{re}")
            finish_poi = get_default_poi()
        logging.info(
            f"{trip_info}: Start Edge: {start_edge}, Lane pos: {start_lane_pos} idx: {start_lane_idx}, Start POI: {start_poi}, way: {start_way_id} - valid: {start_poi_valid}"
            f"- Finish Edge: {finish_edge}, Lane pos: {finish_lane_pos} idx: {finish_lane_idx}, Finish POI: {finish_poi}, way: {finish_way_id} - valid: {finish_poi_valid}")
        if start_coord_valid and finish_coord_valid:
            mapped_edges = pd.concat([mapped_edges, pd.DataFrame([[idx, trip[KEY_STARTLAT], trip[KEY_STARTLONG],
                                                                   start_edge, start_lane_pos, start_poi, start_way_id,
                                                                   trip[KEY_FINLAT],
                                                                   trip[KEY_FINLONG],
                                                                   finish_edge, finish_lane_pos, finish_poi, finish_way_id]],
                                                                 columns=COLUMNS)])
            edge_coords = pd.concat([edge_coords,
                                       pd.DataFrame([[start_edge, trip[KEY_STARTLAT], trip[KEY_STARTLONG]]],
                                                    columns=COLUMNS_LATLONG_EDGES)])
            edge_coords = pd.concat([edge_coords,
                                       pd.DataFrame([[finish_edge, trip[KEY_FINLAT], trip[KEY_FINLONG]]],
                                                    columns=COLUMNS_LATLONG_EDGES)])
        else:
            unmapped_edges = pd.concat([unmapped_edges, pd.DataFrame([[idx, trip[KEY_STARTLAT], trip[KEY_STARTLONG],
                                                                       start_edge, start_lane_pos, start_poi, start_way_id,
                                                                       trip[KEY_FINLAT],
                                                                       trip[KEY_FINLONG],
                                                                       finish_edge, finish_lane_pos, finish_poi, finish_way_id]],
                                                                     columns=COLUMNS)])
            logging.warning(f"{trip_info}:could not be mapped to an edge for cars")
            mapped_trips_test = mapped_trips_test.drop([idx])

    edges_total = len(mapped_edges) + len(unmapped_edges)
    logging.info(
        f"Edges total: {edges_total}, Unmapped: {len(unmapped_edges)}. Ratio: {int(len(unmapped_edges) * 100 / edges_total):.2f}% unmapped.")
    mapped_edges.to_csv(build_output_path(city, f"mapped_edges_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"))
    unmapped_edges.to_csv(build_output_path(city, f"unmapped_edges_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}"))

    rq_creator = CustomerRequestAccess(start_datetime=SIMU_START_DATETIME, sim_duration_seconds=int(
        (SIMU_END_DATETIME - SIMU_START_DATETIME).total_seconds()))
    poi_edge_creator = PoiEdgesAccess()
    for idx, trip in mapped_trips_test.iterrows():
        try:
            time_diff = timediff_seconds(SIMU_START_DATETIME, trip['STARTED_LOCAL'])
            try:
                rq_creator.add_request(CustomerRequest(
                    submit_time_seconds=int(time_diff),
                    from_poi=mapped_edges.query(f"idx == {idx}").iloc[0]['start_poi'],
                    from_edge=mapped_edges.query(f"idx == {idx}").iloc[0]['start_edge'],
                    from_edge_pos=mapped_edges.query(f"idx == {idx}").iloc[0]['start_edge_pos'],
                    to_poi=mapped_edges.query(f"idx == {idx}").iloc[0]['finish_poi'],
                    to_edge=mapped_edges.query(f"idx == {idx}").iloc[0]['finish_edge'],
                    to_edge_pos=mapped_edges.query(f"idx == {idx}").iloc[0]['finish_edge_pos']
                ))
                poi_edge_creator.add_poi_edge(PoiEdge(
                    poi_id=mapped_edges.query(f"idx == {idx}").iloc[0]['start_poi_way_id'],
                    poi_tag=mapped_edges.query(f"idx == {idx}").iloc[0]['start_poi'],
                    edge_id=mapped_edges.query(f"idx == {idx}").iloc[0]['start_edge'],
                    lane_pos=mapped_edges.query(f"idx == {idx}").iloc[0]['start_edge_pos'],
                    lane_idx="_0"
                ))
                poi_edge_creator.add_poi_edge(PoiEdge(
                    poi_id=mapped_edges.query(f"idx == {idx}").iloc[0]['finish_poi_way_id'],
                    poi_tag=mapped_edges.query(f"idx == {idx}").iloc[0]['finish_poi'],
                    edge_id=mapped_edges.query(f"idx == {idx}").iloc[0]['finish_edge'],
                    lane_pos=mapped_edges.query(f"idx == {idx}").iloc[0]['finish_edge_pos'],
                    lane_idx="_0"
                ))
            except IndexError as e:
                logging.error(f"idx({idx}), trip({trip}) - Index error: {e}")
        except RuntimeError as e:
            logging.error(f"Runtime Error: {e}")
    rq_creator.dump(build_output_path(city, "CustomerRequests.xml"))
    poi_edge_creator.dump(build_output_path(city, "POIsEdges.xml"))

    edge_coords_creator = EdgeCoordsAccess()
    for idx, edge in edge_coords.iterrows():
        edge_coords_creator.add_edge_coord(EdgeCoord(
            edge_id=edge["edge_id"],
            lat=edge["lat"],
            long=edge["long"]
        ))
    for edge_coords in additional_edge_coords:
        edge_coords_creator.add_edge_coord(EdgeCoord(
            edge_id=edge_coords["edge_id"],
            lat=edge_coords["lat"],
            long=edge_coords["lon"]
        ))
    for edge_coords in parking_edge_coords:
        edge_coords_creator.add_edge_coord(EdgeCoord(
            edge_id=edge_coords["edge_id"],
            lat=edge_coords["lat"],
            long=edge_coords["lon"]
        ))
    edge_coords_creator.dump(build_output_path(city, "EdgeCoords.xml"))

if __name__ == "__main__":
    print(f"Arguments count: {len(sys.argv)}")
    sumo_working_dir = ""
    for i, arg in enumerate(sys.argv):
        if "-sd=" in arg:
            sumo_working_dir = arg.replace("-sd=", "")
        if "-trips=" in arg:
            trips = arg.replace("-trips=", "")
    main(sumo_working_dir=sumo_working_dir, trips=trips)
