from enum import IntEnum
from Tools.logger import log, elog


class State(IntEnum):
    idling = 0
    to_passenger = 1
    with_passenger = 2
    positioning = 3  # without passenger


class VehicleMonitoring:
    def __init__(self):
        self.__state_history = {}
        self.__current_time_for_logging = 0  # only auto log if sumo_time changes,
        # so only log once per simulation time at max

    def __plausi_check(self):
        total_vehicles, with_passenger, to_passenger, idling, positioning = self.__current_state()
        if total_vehicles != sum([with_passenger, to_passenger, idling, positioning]):
            raise RuntimeError(f"VehID states do not sum up to ({total_vehicles})")

    # check if all states sum up to total_vehicles
    def __current_state(self) -> tuple:
        with_passenger, to_passenger, idling, positioning = 0, 0, 0, 0
        for vehID, history in self.__state_history.items():
            latest = list(history.keys())[-1]
            state = history[latest]
            if state == State.idling:
                idling += 1
            elif state == State.with_passenger:
                with_passenger += 1
            elif state == State.to_passenger:
                to_passenger += 1
            elif state == State.positioning:
                positioning += 1
            else:
                elog(f"state {state} of vehID={vehID} cannot be matched to monitoring state.")
        return len(self.__state_history), with_passenger, to_passenger, idling, positioning

    def __log_current_state__(self):
        total_vehicles, with_passenger, to_passenger, idling, positioning = self.__current_state()
        current_state = {
            "t": self.__current_time_for_logging,
            "total_vehicles": total_vehicles,
            "with_passenger": with_passenger,
            "to_passenger": to_passenger,
            "idling": idling,
            "positioning": positioning

        }
        log(current_state)

    def update_veh_state(self, vehID: str, state: State, sumo_time: int):
        if self.__current_time_for_logging != sumo_time:
            self.__log_current_state__()
            self.__current_time_for_logging = sumo_time
        if vehID not in self.__state_history:
            self.__state_history[vehID] = {sumo_time: state}
            return
        self.__state_history[vehID][sumo_time] = state
        self.__plausi_check()

