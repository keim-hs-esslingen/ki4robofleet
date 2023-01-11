import pandas as pd
from .base_algorithm import BaseAlgorithm
from .Distribution.simple_distribution_algorithm import SimpleDistributionAlgorithm, EdgeCoordinates, SectorCoordinates
from KI4RoboRoutingTools.Prediction_Model.TrainingData.training_data import TrainingData

class AlgorithmFactory:
    def __init__(self,
                 edge_coordinates: EdgeCoordinates = EdgeCoordinates(),
                 sector_coordinates: SectorCoordinates = SectorCoordinates,
                 init_vehicle_pos_edges=None,
                 training_data: TrainingData=None):
        if init_vehicle_pos_edges is None:
            init_vehicle_pos_edges = {}
        self.__algorithms = {
            "simple_distribution": SimpleDistributionAlgorithm
        }
        self.__edge_coordinates = edge_coordinates
        self.__sector_coordinates = sector_coordinates
        self.__init_vehicle_pos_edges = init_vehicle_pos_edges
        print("WARNING: to-do handle target_distribution differently")
        # think about how to handle the target distribution to-do
        # need some kind of relative time associated with recent values
        # so maybe pass complete old values to algorithm and let it decide what to do
        self.__training_data = training_data

    def get_algorithm(self, algorithm_name: str) -> BaseAlgorithm:
        if algorithm_name in self.__algorithms:
            # make type checks!!
            return self.__algorithms[algorithm_name](self.__edge_coordinates,
                                                     self.__sector_coordinates,
                                                     self.__init_vehicle_pos_edges,
                                                     self.__training_data)
        else:
            raise ValueError(f"Algorithm {algorithm_name} not found")
