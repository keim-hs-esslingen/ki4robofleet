#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# This Script provides basic Simulation functions with logging
# =============================================================================


from Net.point_of_interest import Point_of_Interest
from typing import List, Dict
from Tools.logger import log, elog, dlog
from Tools.XMLogger import xlog
from Tools.check_sumo import sumo_available
from Moving.request import Request
from Moving.vehicles import Vehicle

sumo_available()
import traci  # noqa


def simulation_step() -> int:
    try:
        traci.simulationStep()
    except Exception as e:
        elog(f"step error {e}")
        exit()
    return int(traci.simulation.getTime())


def dispatch(taxi, reservations):
    if type(reservations) == str:
        reservations = [reservations]
    try:
        #nextPoi = reservations[]
        traci.vehicle.dispatchTaxi(taxi, reservations)
        #print("RESERVIERUNGSLISTE: ",str(reservations[0]))


        xlog(name="dispatch", vehicle=taxi, reservations=str(reservations))
    except Exception as e:
        current_reservations = traci.person.getTaxiReservations(0)
        new_reservation_ids = [r.id for r in current_reservations]
        sumo_time = int(traci.simulation.getTime())
        elog(f"dispatch error with {taxi}/{reservations}\n{e}")
        xlog(
            name="dispatch_error",
            time=sumo_time,
            error=e,
            reservations=str(new_reservation_ids),
        )
        return False
    return True


def add_route(req: Request):
    """
    generate a route,
    - necessary for vehicle creation
    """
    start = req.from_edge
    tgt = req.to_edge
    stage = traci.simulation.findRoute(start, tgt)
    assert stage and len(stage.edges) > 2
    rid = f"rt_{req.idx}"
    traci.route.add(rid, stage.edges)
    return rid


def add_and_move_vehicle(vehID, req: Request, t=0):
    """
    generate taxi and move taxi to start-poi of request
    """
    rid = add_route(req)
    try:
        traci.vehicle.add(vehID, routeID=rid, typeID="taxi")
        log(f"new vehicle {vehID}")
    except Exception as e:
        elog(f"new vehicle error: {e}")
        return False

    try:
        toPoiColor = req.to_poi.color
        print("add_and_move_vehicle",to_poi.poi_type)
        #set vehicle color to target POI
        traci.vehicle.setColor(
            vehID, (int(toPoiColor[0]), int(toPoiColor[1]), int(toPoiColor[2]))
        )
        traci.vehicle.moveTo(vehID, req.from_poi.road_lane, req.oldpos)
        dlog(f"moved vehicle {vehID} {req.from_poi.road_lane}: {req.oldpos}")
    except Exception as e:
        elog(f"move {vehID} error: {e};")
        return False

    xlog(name="vehicle", time=t, vehicle=vehID, cmd="init", req_id=req.idx)
    return True


def add_and_reset_vehicle(veh: Vehicle, t=0):
    """
    generate taxi and move taxi to start-poi of request
    """
    try:
        traci.vehicle.add(veh.vehID, routeID="", typeID="taxi")
        log(f"new vehicle {veh.vehID}")
    except Exception as e:
        # elog(f"new vehicle error: {e}")
        pass

    try:
        print("RESET:")
        traci.vehicle.setColor(veh.vehID, (0, 255, 0))
        traci.vehicle.moveTo(veh.vehID, veh.edge, veh.pos)
        dlog(f"moved vehicle {veh.vehID} {veh.edge}: {veh.pos}")
    except Exception as e:
        elog(f"move {veh.vehID} at {t} to <{veh.edge}> error: {e};")
        return False

    xlog(name="vehicle", time=t, vehicle=veh.vehID, cmd="reset")
    return True


def add_and_route_vehicle(vehID, to_poi: Point_of_Interest, t=0):
    """
    generate taxi and move taxi to start-poi of request
    """
    try:
        traci.vehicle.add(vehID, routeID=to_poi.route, typeID="taxi")
        
        # log(f"new vehicle {vehID}")
    except Exception as e:
        elog(f"new vehicle error {e}")
        return False

    try:
        toPoiColor = to_poi.color
        print("add_and_route_vehicle",to_poi.poi_type)
        print(toPoiColor)
        traci.vehicle.setColor(
            vehID, (int(toPoiColor[0]), int(toPoiColor[1]), int(toPoiColor[2]))
        )
        traci.vehicle.moveTo(vehID, to_poi.road_lane, to_poi.pos)
        # dlog(f"moved vehicle {vehID} {to_poi.road_lane}: {to_poi.pos}")
    except Exception as e:
        elog(f"move {vehID} error {e};")
        return False

    xlog(name="vehicle", time=t, vehicle=vehID, cmd="init", poi=to_poi.idx)
    return True


def add_person_request(personID, req: Request):
    """
    generate person and enter a request
    - the request is converted to SUMO-reservation internally
    """
    req.personID = None
    try:
        traci.person.add(
            personID, req.from_edge, pos=req.oldpos, typeID="DEFAULT_PEDTYPE"
        )
    except Exception as e:
        elog(f"add person {personID} at {req.from_edge} error {str(e)}")
        return False

    try:
        traci.person.appendDrivingStage(personID, req.to_edge, lines="taxi")
    except Exception as e:
        elog(f"taxi person {personID} at {req.to_edge} error {str(e)}")
        return False

    req.personID = personID
    req.reservation = None
    return True
