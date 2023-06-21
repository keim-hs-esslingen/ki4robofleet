import pandas as pd
from KI4RoboRoutingTools.Prediction_Model.Algorithms.base_algorithm import BaseAlgorithm
from KI4RoboRoutingTools.Prediction_Model.Algorithms.Distribution.sector_distribution_model import SectorDistributionModel
from KI4RoboRoutingTools.Prediction_Model.edge_sector_converter import EdgeSectorConverter, EdgeCoordinates, Coordinates, SectorCoordinates, Sector
from KI4RoboRoutingTools.Prediction_Model.TrainingData.training_data import TrainingData

STATIC_THRESHOLD_ADDITION = 0.0000000001
class SimpleDistributionAlgorithm(BaseAlgorithm):
    def __init__(self,
                 edge_coords: EdgeCoordinates,
                 sector_coords: SectorCoordinates,
                 init_vehicle_pos_edges: dict,
                 training_data_for_target_dist: TrainingData):
        super().__init__()
        self.__edge_coords = edge_coords
        self.__sector_coords = sector_coords
        self.__converter = EdgeSectorConverter(edge_coords=edge_coords, sector_coords=sector_coords)
        # convert vehicle positions from dict to dict with value sector tuple and key vid
        vehicle_sectors = {}
        for vid, edge_id in init_vehicle_pos_edges.items():
            vehicle_sectors[vid] = self.__converter.to_sector(edge_id)
        self.__distribution_model = SectorDistributionModel(vehicle_pos_sectors=vehicle_sectors,
                                                            sectors_shape=sector_coords.get_sectors_shape())
        self.__training_data = training_data_for_target_dist

        self.__most_underserved_sector = None
        self.__calculate_underserved_sector()

    def __calculate_underserved_sector(self):
        diff_list = self.__distribution_model.diff_list()
        greatest_diff_sector = diff_list.iloc[0].to_dict()
        lowest_diff_sector = diff_list.iloc[-1].to_dict()
        greatest_diff_value = greatest_diff_sector["DIFF"]
        lowest_diff_value = lowest_diff_sector["DIFF"]
        diff = greatest_diff_value - lowest_diff_value
        diff_threshold = self.__distribution_model.calculate_diff_threshold() + STATIC_THRESHOLD_ADDITION
        sector = Sector(row=greatest_diff_sector["ROW"], col=greatest_diff_sector["COL"])
        # check if all values in diff are 0, so there is no underserved sector
        if diff_list["DIFF"].std() == 0:
            if self.__most_underserved_sector is not None:
                print("Update: No underserved sector, distribution is balanced")
                self.__most_underserved_sector = None
                return
        # equal distribution, but not all values are 0, see calculation in distribution model
        # abs values because of boundary case
        elif diff <= diff_threshold and abs(greatest_diff_value) != abs(lowest_diff_value):
            if self.__most_underserved_sector is not None:
                print("Update: No underserved sector, distribution diff is below threshold (#vehicles - #sectors / #vehicles * #sectors)")
                self.__most_underserved_sector = None
                return
        else:
            if sector != self.__most_underserved_sector:
                print(f"Update: most_underserved_sector: {sector}")
                self.__most_underserved_sector = sector

    # can throw ValueError
    def get_edge(self):
        if self.__most_underserved_sector is None:
            return None
        # return representative edge of sector
        return self.__converter.to_edge(self.__most_underserved_sector)

    # can throw ValueError
    def push_edge(self, vid, edge_id: str, time: int):
        super().push_edge(vid, edge_id, time) # check if still needed
        # convert edge to sector, may throw if edge_id not contained
        sector = self.__converter.to_sector(edge_id)
        # set target distribution
        target_distribution_df = self.__training_data.get_record(rel_time_seconds=time, interpolated=True)
        # set target_distribution from values in target_distribution_df
        target_distribution = pd.DataFrame(data=0.0,
                                           index=range(target_distribution_df["ROW"].min(),
                                                       target_distribution_df["ROW"].max() + 1),
                                           columns=range(target_distribution_df["COL"].min(),
                                                         target_distribution_df["COL"].max() + 1),
                                           dtype=float)
        for index, row in target_distribution_df.iterrows():
            target_distribution.loc[row["ROW"], row["COL"]] = row["REQUESTS"]
        self.__distribution_model.set_target_distribution(target_distribution)
        # update distribution model
        self.__distribution_model.update_vehicle_sector(row=sector.row(), col=sector.col(), vid=vid)
        # update most underserved sector (this is how this algorithm works)
        self.__calculate_underserved_sector()
