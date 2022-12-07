import traci
from enum import IntEnum

class TaxiState(IntEnum):
    # from https://sumo.dlr.de/docs/Simulation/Taxi.html#gettaxifleet
    Empty = 0,  # also contains EmptyButOptimizing
    Pickup = 1,
    Occupied = 2,
    PickupAndOccupied = 3,
    # custom state
    EmptyButOptimizing = 4

    def __str__(self):
        return str(self.name)


class TaxiFleetStateWrapper:
    def __init__(self):
        self.fleet = {}
        # all taxis must be in empty state at the beginning
        # information (Single Source of Truth) comes from traci.vehicle.getTaxiFleet(taxiState)
        invalid_start_states = [TaxiState.Pickup, TaxiState.Occupied, TaxiState.PickupAndOccupied]
        for invalid_start_state in invalid_start_states:
            invalid_vehIDs = list(traci.vehicle.getTaxiFleet(invalid_start_state))
            if len(invalid_vehIDs) > 0:
                raise Exception(f"Initialize TaxiFleetState at very beginning of the simulation with TaxiState.Empty. "
                                f"Invalid start state: {str(invalid_start_state)} of taxis {invalid_vehIDs}")
        fleet = list(traci.vehicle.getTaxiFleet(TaxiState.Empty))
        for vehID in fleet:
            self.__update_state(vehID, TaxiState.Empty)

    def __update_state(self, vehID: str, state: TaxiState):
        self.fleet[vehID] = state

    def __update(self):
        for vehID in list(traci.vehicle.getTaxiFleet(TaxiState.Pickup)):
            self.__update_state(vehID, TaxiState.Pickup)
        for vehID in list(traci.vehicle.getTaxiFleet(TaxiState.Occupied)):
            self.__update_state(vehID, TaxiState.Occupied)
        for vehID in list(traci.vehicle.getTaxiFleet(TaxiState.PickupAndOccupied)):
            self.__update_state(vehID, TaxiState.PickupAndOccupied)

    def set_optimizing_state(self, vehID: str):
        self.__update_state(vehID, TaxiState.EmptyButOptimizing)

    # update state of all taxis and return requested state
    def get_taxi_fleet(self, taxiState: TaxiState) -> list:
        self.__update()
        concat_list = []
        # empty state contains also TaxiState.EmptyButOptimizing
        if taxiState == TaxiState.Empty:
            concat_list.append(list(traci.vehicle.getTaxiFleet(TaxiState.Empty)))
            concat_list.append(list(traci.vehicle.getTaxiFleet(TaxiState.EmptyButOptimizing)))
            return concat_list
        else:
            return list(traci.vehicle.getTaxiFleet(taxiState))

