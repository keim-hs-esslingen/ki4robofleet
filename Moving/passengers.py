#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: March 2021
# License: MIT License
# =============================================================================
# This Script provides the function current_passengers()
# See also:
# https://sumo.dlr.de/docs/Specification/Persons.html
# https://sumo.dlr.de/pydoc/traci._person.html
# =============================================================================

from typing import List, Dict

from Moving.request import Request
from Tools.check_sumo import sumo_available
from Tools.logger import log
from Moving.vehicles import Vehicle

sumo_available()
import traci  # noqa


# PERSON COLORS
COLOR_FULFILLING = (245, 215, 66)

COLOR_WALKING = (0, 0, 255)
COLOR_WAITING = COLOR_FULFILLING
COLOR_DRIVING = (252, 139, 10)


# returns: list of driving passengers, dict entered {vehID: personID}, dict left {vehID: personID}
def update_entering_and_leaving(
    driving: List[str],
    open_requests: List[Request],
    vehicle_positions: Dict[str, Vehicle],
) -> tuple:
    """
    store all personIDs that are in any vehicles
    - if person occurs for the first time: call req.enter
    - if person does not occur anymore: call req.leave

    Parameters:
    - driving: list of persons from the last time

    """
    sumo_time = int(traci.simulation.getTime())

    current_driving = []
    entered = {}
    left = {}
    full_vehicle_id_list = traci.vehicle.getIDList()
    for vehID in full_vehicle_id_list:
        # get person in taxi for each taxi
        pl = traci.vehicle.getPersonIDList(vehID)
        for personID in pl:
            # if person not yet listed in "driving" list: person enters vehicle
            if personID not in driving:
                log(f"{personID} enters {vehID}")
                for req in open_requests:
                    if req.personID == personID:
                        traci.vehicle.setColor(vehID, (int(req.to_poi.color[0]), int(req.to_poi.color[1]), int(req.to_poi.color[2])))
                        req.enter(vehID, sumo_time, vehicle_positions[vehID].dist)
                        entered[vehID] = personID
                        break
            # update list of persons currently driving
            current_driving.append(personID)

    for personID in driving:
        # if person is not in "currently_driving" list but was in arg "driving" list, person must have left taxi
        if personID not in current_driving:
            for req in open_requests:
                if req.personID == personID:
                    req.leave(sumo_time, vehicle_positions[req.vehID].dist)
                    left[vehID] = personID
                    break

    return current_driving, entered, left
