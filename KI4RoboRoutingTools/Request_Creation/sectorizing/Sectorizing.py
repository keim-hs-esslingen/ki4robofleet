import pandas as pd
import numpy as np
import math
from KI4RoboRoutingTools.Request_Creation.sumohelper.Coord2EdgeConverter import EdgeFinder


PERCENTAGE_OF_NONEMPTY_SECTORS = 20

def sector_hints(distance_NS_km: int, distance_EW_km: int, row_count: int, hours: int, step_meters: int = -1):
    if step_meters == -1:
        cols = round(math.sqrt(row_count * distance_EW_km / (hours * 100 / 20 * distance_NS_km)))
        rows = round(distance_NS_km / distance_EW_km * cols)
        calculated_step_meters = distance_EW_km * 1000 / cols
        print(f"Recommended step size ({calculated_step_meters} m) that {PERCENTAGE_OF_NONEMPTY_SECTORS}% of the sectors per hour have non-empty request counts")
        return rows, cols, int(calculated_step_meters)
    else:
        rows = distance_NS_km * 1000 / step_meters
        cols = distance_EW_km * 1000 / step_meters
        if rows < 2 or cols < 2:
            raise Exception("step_meters parameter is too big. Choose e.g. 500 = 500m")
        return round(rows), round(cols), int(step_meters)


def aggregated_requests(df: pd.DataFrame, zero_req_padding: bool, fix_row_col_count: tuple = (-1, -1)):
    if zero_req_padding:
        if fix_row_col_count == (-1, -1):
            rowmax = df['ROW'].max() + 1
            colmax = df['COL'].max() + 1
        else:
            rowmax, colmax = fix_row_col_count
        if colmax > 20 or rowmax > 20:
            print("Warning: ROW or COL count is higher than 20. Processing will need much time!")
        # df_ret = pd.DataFrame(data=[], columns=['WEEKDAY', 'HOUR', 'ROW', 'COL', 'REQUESTS'], dtype="int32")
        df_ret = pd.DataFrame(data=0,
                              index=range(colmax * rowmax * (
                                          df['WEEKDAY'].max() - df['WEEKDAY'].min() + 1) * 24),
                              columns=['WEEKDAY', 'HOUR', 'ROW', 'COL', 'REQUESTS'], dtype="int32")
        print(f"Aggregated requests will have {len(df_ret)} rows")
        i = 0
        for col in range(0, colmax):
            for row in range(0, rowmax):
                for weekday in range(df['WEEKDAY'].min(), df['WEEKDAY'].max() + 1):
                    for hour in range(0, 24):
                        count = df.query(
                            f"WEEKDAY == {weekday} and HOUR == {hour} and COL == {col} and ROW == {row}").shape[0]
                        df_ret.loc[i, ['WEEKDAY', 'HOUR', 'ROW', 'COL', 'REQUESTS']] = [weekday, hour, row, col,
                                                                                          count]
                        i += 1
    else:
        df_ret = pd.DataFrame(data=[], columns=['WEEKDAY', 'HOUR', 'ROW', 'COL', 'REQUESTS'], dtype="int32")
        for idx, item in df.iterrows():
            weekday, hour, row, col = item['WEEKDAY'], item['HOUR'], item['ROW'], item['COL']
            if df_ret.query(f"WEEKDAY == {weekday} and HOUR == {hour} and COL == {col} and ROW == {row}").shape[0] == 0:
                count = df.query(f"WEEKDAY == {weekday} and HOUR == {hour} and COL == {col} and ROW == {row}").shape[0]
                temp_df_sector = pd.DataFrame(data=[[weekday, hour, row, col, count]],
                                              columns=['WEEKDAY', 'HOUR', 'ROW', 'COL', 'REQUESTS'], dtype="int32")
                df_ret = pd.concat([df_ret, temp_df_sector])
                continue
            else:
                continue
    avg_requests_per_entry = df_ret['REQUESTS'].mean()
    print(f"Average requests per entry: {avg_requests_per_entry}, Max: {df_ret['REQUESTS'].max()}")
    return df_ret


def metrics_per_sector(row, col):
    pass


class Sectorizer():
    def __init__(self, df: pd.DataFrame, row_count: int, col_count: int, edge_finder: EdgeFinder):
        self._row_count = row_count
        self._col_count = col_count
        self._df = df
        self._edge_finder = edge_finder
        self._start_lat_min, self._start_lat_max = df['STARTLAT'].min(), df['STARTLAT'].max()
        self._start_lon_min, self._start_lon_max = df['STARTLONG'].min(), df['STARTLONG'].max()
        self._lat_step = (self._start_lat_max - self._start_lat_min) / self._row_count
        self._lon_step = (self._start_lon_max - self._start_lon_min) / self._col_count
        self._repr_edge_coords = []

    def _find_edge_in_center_of_sector(self, row, col):
        # get center of sector
        lat = self._start_lat_min + self._lat_step * (row + 0.5)
        lon = self._start_lon_min + self._lon_step * (col + 0.5)
        edge, _, _ = self._edge_finder.findNearestEdge(lat=lat, long=lon)
        if edge not in self._repr_edge_coords:
            self._repr_edge_coords.append({"edge_id": edge, "lat": lat, "lon": lon})
        return edge

    def enrich_sectors(self) -> pd.DataFrame:
        """
        Enriches the dataframe with the sector information (ROW, COL) (not in place)
        """
        df_sector = pd.DataFrame({'ROW': [], 'COL': []}, dtype="int32")
        for idx, item in self._df.iterrows():
            # Calculate row and col from lat and long
            row = int((item["STARTLAT"] - self._start_lat_min) / self._lat_step)
            if row == self._row_count:
                row -= 1
            col = int((item["STARTLONG"] - self._start_lon_min) / self._lat_step)
            if col == self._col_count:
                col -= 1
            temp_df_sector = pd.DataFrame(data=[[row, col]], index=[idx], columns=['ROW', 'COL'],
                                          dtype="int32")
            df_sector = pd.concat([df_sector, temp_df_sector])
        df_ret = self._df.join(df_sector)
        return df_ret

    def bbox_of_sectors(self) -> list:
        """
        Returns a list of dicts of the bounding box of each sector
        bbox=[min_lon/left, min_lat/bottom, max_lon/right, max_lat/top] e.g. [-180, -90, 180, 90]
        e.g.
        [
            ...
            { "row": 0, "col": 3, "bbox": [47.5, 19.0, 47.6, 19.1], "representative_edge": "#12345" },
            { "row": 0, "col": 4, "bbox": [47.5, 19.1, 47.6, 19.2], "representative_edge": "-#51242" },
            ...
        ]
        """
        bbox_list = []
        for row in range(0, self._row_count):
            for col in range(0, self._col_count):
                bbox_list.append({
                    "row": row,
                    "col": col,
                    "bbox": [
                        self._start_lon_min + col * self._lon_step,
                        self._start_lat_min + row * self._lat_step,
                        self._start_lon_min + (col + 1) * self._lon_step,
                        self._start_lat_min + (row + 1) * self._lat_step
                    ],
                    "representative_edge": self._find_edge_in_center_of_sector(row, col)
                })
        return bbox_list

    def additional_edge_coords(self) -> list:
        return self._repr_edge_coords
