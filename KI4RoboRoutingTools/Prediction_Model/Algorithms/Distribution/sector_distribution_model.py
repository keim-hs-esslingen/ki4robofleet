import pandas as pd
from KI4RoboRoutingTools.Prediction_Model.sector import Sector

class SectorDistributionModel:
    def __init__(self, vehicle_pos_sectors: dict, sectors_shape: tuple):
        # check if tuple has two elements, if not raise error
        if len(sectors_shape) != 2:
            raise AttributeError(f"sectors_shape must have two elements, passed {len(sectors_shape)}")
        self.__shape = sectors_shape
        self.__dict_vid_sectors = vehicle_pos_sectors
        self.__target_distribution_norm = pd.DataFrame(data=0.0, index=range(sectors_shape[0]),
                                                       columns=range(sectors_shape[1]), dtype=float)
        self.__current_distribution_vehicle_count = pd.DataFrame(data=0, index=range(sectors_shape[0]),
                                                                 columns=range(sectors_shape[1]), dtype=int)
        self.__current_distribution_norm = pd.DataFrame(data=0.0, index=range(sectors_shape[0]),
                                                        columns=range(sectors_shape[1]), dtype=float)
        # calculate current distribution from self.__vehicle_pos_sectors
        for vid, sector in self.__dict_vid_sectors.items():
            self.__current_distribution_vehicle_count.loc[sector.row(), sector.col()] += 1
        self.__calculate_current_distribution()

    def __calculate_current_distribution(self):
        # check if len of vehicle_positions is 0
        if len(self.__dict_vid_sectors) == 0:
            print("WARNING: No vehicles in the model. Add with 'update_vehicle_sector(row, col, vid)'")
            return
        # calculate current distribution by dividing current vehicle distribution by total number of vehicles
        self.__current_distribution_norm = self.__current_distribution_vehicle_count / len(self.__dict_vid_sectors)

    def set_target_distribution(self, target: pd.DataFrame):
        if target.shape != self.__shape:
            raise AttributeError(f"target must have shape {self.__shape}, passed {target.shape}")
        # normalize target distribution and set it as __target_distribution
        self.__target_distribution_norm = target / target.sum().sum()

    def update_vehicle_sector(self, row: int, col: int, vid):
        # check if vid is already in the model
        if vid in self.__dict_vid_sectors:
            # decrement count in current distribution in the old sector where the vehicle was
            old_sector = self.__dict_vid_sectors[vid]
            self.__current_distribution_vehicle_count.loc[old_sector.row(), old_sector.col()] -= 1
        # update vehicle position and current vehicle distribution
        self.__dict_vid_sectors[vid] = Sector(row, col)
        self.__current_distribution_vehicle_count.loc[row, col] += 1
        self.__calculate_current_distribution()

    # check if diff balanced, but not all 0:
    # threshold-calulation formula: (#vehicles - #sectors)/(#vehicles * #sectors)
    def calculate_diff_threshold(self) -> float:
        return (len(self.__dict_vid_sectors) - self.__shape[0] * self.__shape[1]) / \
               (len(self.__dict_vid_sectors) * self.__shape[0] * self.__shape[1])

    def diff_list(self):
        diff = self.__target_distribution_norm - self.__current_distribution_norm
        order = pd.DataFrame(data=0, index=range(diff.shape[0] * diff.shape[1]),
                             columns=["ROW", "COL", "DIFF"])
        i = 0
        for row_idx, row in diff.iterrows():
            for col_idx, value in row.items():
                order.loc[i, ['ROW', 'COL', 'DIFF']] = [row_idx, col_idx, value]
                i+=1
        return order.sort_values(by=['DIFF'], ascending=False)