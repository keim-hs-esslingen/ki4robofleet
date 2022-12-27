#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# This Script converts requests to SUMO-reservations
# and stores reservations in requests
# =============================================================================


from os import fwalk
from Net.point_of_interest import Point_of_Interest
from typing import List, Dict
from Tools.logger import log, elog, dlog
from Tools.XMLogger import xlog
from Tools.check_sumo import sumo_available
from Moving.request import Request
import Moving.sumo_functions as sf
from Moving.passengers import update_entering_and_leaving
from Moving.vehicles import Vehicle
from Moving.taxi_fleet_state_wrapper import TaxiFleetStateWrapper, TaxiState
from Moving.vehicle_monitoring import VehicleMonitoring, State
from KI4RoboRoutingTools.Prediction_Model.Algorithms.algorithm_factory import AlgorithmFactory

from Project.project_data import ProjectConfigData

sumo_available()
import traci  # noqa


def check_requests(requests: List[Request], logging: bool = False):
    open_requests = []
    sumo_time = sf.simulation_step()
    for i, req in enumerate(requests):
        personID = f"p_{i:04d}"
        req.reset()
        if sf.add_person_request(personID, req):
            open_requests.append(req)

    all = []
    while sumo_time < 100 and len(all) < len(open_requests):
        try:
            sumo_time = sf.simulation_step()
            all = traci.person.getTaxiReservations(0)
        except Exception as e:
            pass

    elog(f"t={sumo_time} getTaxiReservations - cnt= {len(all)}")
    assert len(all) > 0
    reservations = sorted(all, key=lambda r: int(r.id))

    clean_requests = []
    for res in reservations:
        personID = res.persons[0]
        for req in open_requests:
            if req.personID == personID:
                req.reservation = res
                clean_requests.append(req)
                if logging:
                    xlog(
                        name="reservation",
                        person=personID,
                        reservation=res.id,
                        request=req.idx,
                    )
                break

    return clean_requests

def add_route_to_poi(start, poi: Point_of_Interest):
    """
    generate a route,
    - necessary for parking
    """
    stage = traci.simulation.findRoute(start, poi.road)
    assert stage and len(stage.edges) > 2
    rid = f"to_poi_{poi.idx}"
    traci.route.add(rid, stage.edges)
    return rid


def is_available(vehID, full_vehicle_id_list, un_available, sumo_time):
    if vehID not in full_vehicle_id_list:
        if vehID not in un_available:
            un_available.append(vehID)
            # sf.add_and_reset_vehicle(vehicle_positions[vehID], sumo_time)
            elog(f"vehicle {vehID} not available at {sumo_time}")
        return False

    if vehID in un_available:
        log(f"vehicle {vehID} re-available at {sumo_time}")
        un_available.remove(vehID)

    return True


def shared_strategy(data: ProjectConfigData):
    """
    using shared routes
    - one taxi per shared route
    - all reservations out at the beginning
    - dispatches one or two reservations

    """
    parking = data.parking
    requests = data.requests
    routes = data.routes

    # add routes to sumo and store route-id in poi
    # used to initially send taxis to parking places
    for poi in parking:
        poi.route = add_route_to_poi(data.clean_edge, poi)

    open_requests = check_requests(requests, logging=True)

    vehicle_positions: Dict[Vehicle] = {}
    requests_dict = {}

    # map req.idx to requests
    for r in requests:
        r.schedule_time = None
        requests_dict[r.idx] = r

    # distribute reservattion
    # - one route - one vehicle/taxi
    vehicle_reservations = {}
    for i, route in enumerate(routes):
        vehID = f"taxi_{i:04d}"
        vehicle_reservations[vehID] = route.reservations
        xlog(name="route", vehicle=vehID, route=str(route.reservations))
        vehicle_positions[vehID] = Vehicle(vehID=vehID)

    # list of all vehicle IDs
    vehicle_ids = vehicle_reservations.keys()

    # init all taxis
    no_park = len(parking)

    for i, vehID in enumerate(vehicle_ids):
        idx = i
        while idx >= no_park:
            idx -= no_park
        poi = parking[idx]
        sf.add_and_route_vehicle(vehID, poi)

    sumo_time = 0

    # list of passengers currently driving in vehicles
    driving = []
    un_fullfilled = []
    un_available = []

    current_reservations = traci.person.getTaxiReservations(0)
    reservations_ids = [r.id for r in current_reservations]

    timeout = int(data.epoch_timeout)
    while sumo_time < timeout:
        sumo_time = sf.simulation_step()
        if sumo_time % 100 == 0:
            dlog(f"step {sumo_time}")
        full_vehicle_id_list = traci.vehicle.getIDList()
        empty_fleet = list(traci.vehicle.getTaxiFleet(TaxiState.Empty))

        current_reservations = traci.person.getTaxiReservations(0)
        new_reservation_ids = [r.id for r in current_reservations]
        scheduled_ids = [r for r in reservations_ids if r not in new_reservation_ids]
        if scheduled_ids:
            xlog(
                name="reservation_removed", time=sumo_time, scheduled=str(scheduled_ids)
            )
        reservations_ids = new_reservation_ids

        # iterate all taxis
        for vehID in vehicle_ids:

            if not is_available(
                vehID=vehID,
                full_vehicle_id_list=full_vehicle_id_list,
                un_available=un_available,
                sumo_time=sumo_time,
            ):
                continue

            # we have pending reservation AND (vehicle is not yet created OR it is created AND empty)
            if vehicle_reservations[vehID] and vehID in empty_fleet:

                reservations = vehicle_reservations[vehID]
                first = reservations[0][0]
                first_req: Request = requests_dict[first]
                if first_req.submit_time > sumo_time:
                    continue

                # stores all reservation.ids to be dispatched
                reservations = []

                # trip contains list of shared request.idx
                trip = vehicle_reservations[vehID].pop(0)
                dlog(
                    f"{sumo_time} vehicle {vehID} schedules {trip} has {len(vehicle_reservations[vehID])} trips"
                )

                trip_set = set(trip)

                for t in trip_set:
                    # get the request object
                    req = requests_dict[t]

                    # schedule the request --> logging
                    req.schedule(vehID, sumo_time)

                for t in trip:
                    # get the request object
                    req = requests_dict[t]
                    # append the reservation id
                    reservations.append(req.reservation.id)

                # send list of reservations to vehicle
                sf.dispatch(vehID, reservations)

        # monitor the distances driven
        for vehID in full_vehicle_id_list:
            if vehID in vehicle_positions:
                vehicle_positions[vehID].update()

        # check entering and leaving passengers
        driving, entered, left = update_entering_and_leaving(
            driving=driving,
            open_requests=open_requests,
            vehicle_positions=vehicle_positions,
        )

        # check if we have fullfilled all requests
        un_fullfilled = [r for r in open_requests if r.exit_time == 0]
        if not un_fullfilled:
            sumo_time = timeout

    if Request.manager:
        d_full_mileage = 0
        for vehID, vehicle in vehicle_positions.items():
            d_full_mileage += vehicle.dist
        Request.manager.requests_finished(d_full_mileage)

    log(f"Stop at {sumo_time} with {len(un_fullfilled)} unfullfilled requests")


def simple_strategy(data: ProjectConfigData):
    """
    using shared routes
    - one taxi per shared route
    - all reservations out at the beginning
    - dispatches one or two reservations

    """
    parking = data.parking
    requests = data.requests

    # add routes to sumo and store route-id in poi
    # used to initially send taxis to parking places
    for poi in parking:
        poi.route = add_route_to_poi(data.clean_edge, poi)

    vehicle_positions: Dict[Vehicle] = {}
    requests_dict = {}

    # map req.idx to requests
    for r in requests:
        r.schedule_time = None
        requests_dict[r.idx] = r

    # list of all vehicle IDs
    monitoring = VehicleMonitoring()
    vehicle_ids = []
    no_of_parking = len(parking)
    for i in range(data.no_of_vehicles):
        pidx = i % no_of_parking
        parking_poi = parking[pidx]
        vehID = f"taxi_{i:04d}"
        sf.add_and_route_vehicle(vehID, parking_poi)
        vehicle_ids.append(vehID)
        vehicle_positions[vehID] = Vehicle(vehID=vehID)
        monitoring.update_veh_state(vehID=vehID, state=State.idling, sumo_time=0)

    open_requests = check_requests(requests)
    sumo_time = 0

    # list of passengers currently driving in vehicles
    driving = []
    un_fullfilled = []

    taxi_fleet_state = TaxiFleetStateWrapper()

    timeout = int(data.epoch_timeout)
    while sumo_time < timeout:
        sumo_time = sf.simulation_step()
        full_vehicle_id_list = traci.vehicle.getIDList()
        empty_fleet = taxi_fleet_state.get_taxi_fleet(taxiState=TaxiState.Empty)

        current_open_requests = [
            req
            for req in open_requests
            if not req.schedule_time and req.submit_time <= sumo_time
        ]
        while current_open_requests and empty_fleet:
            vehID = empty_fleet.pop()
            req = current_open_requests.pop()
            fromPoiColor = req.from_poi.color
            # set vehicle color according to POI color
            
            traci.vehicle.setColor(
                vehID, (int(fromPoiColor[0]), int(fromPoiColor[1]), int(fromPoiColor[2]))
            )

            sf.dispatch(vehID, [req.reservation.id])
            # schedule the request --> logging
            req.schedule(vehID, sumo_time)
            monitoring.update_veh_state(vehID=vehID, state=State.to_passenger, sumo_time=sumo_time)

        left_vehicles = [
            vehID for vehID in vehicle_ids if vehID not in full_vehicle_id_list
        ]
        for vehID in left_vehicles:
            xlog(name="vehicle", time=sumo_time, vehicle=vehID, cmd="left")
            vehicle_ids.remove(vehID)

        # monitor the distances driven
        for vehID in full_vehicle_id_list:
            if vehID in vehicle_positions:
                vehicle_positions[vehID].update()

        # check entering and leaving passengers
        driving, entered, left = update_entering_and_leaving(
            driving=driving,
            open_requests=open_requests,
            vehicle_positions=vehicle_positions,
        )
        [monitoring.update_veh_state(vehID=vehID, state=State.with_passenger, sumo_time=sumo_time)
         for vehID in entered.keys()]
        [monitoring.update_veh_state(vehID=vehID, state=State.idling, sumo_time=sumo_time)
         for vehID in left.keys()]

        # check if we have fullfilled all requests
        un_fullfilled = [r for r in open_requests if r.exit_time == 0]
        if not un_fullfilled:
            sumo_time = timeout

    if Request.manager:
        d_full_mileage = 0
        for vehID, vehicle in vehicle_positions.items():
            d_full_mileage += vehicle.dist
        Request.manager.requests_finished(d_full_mileage)

    log(f"Stop at {sumo_time} with {len(un_fullfilled)} unfullfilled requests")


def look_ahead_strategy(data: ProjectConfigData):
    """
    using shared routes
    - one taxi per shared route
    - all reservations out at the beginning
    - dispatches one or two reservations

    """
    parking = data.parking
    requests = data.requests

    try:
        look_ahead_time = int(data.look_ahead_time)
    except:
        look_ahead_time = 100

    elog(f"Look ahead {look_ahead_time/60} min.")

    # add routes to sumo and store route-id in poi
    # used to initially send taxis to parking places
    for poi in parking:
        poi.route = add_route_to_poi(data.clean_edge, poi)

    open_requests = check_requests(requests)

    vehicle_positions: Dict[Vehicle] = {}
    requests_dict = {}

    # map req.idx to requests
    for r in requests:
        r.schedule_time = None
        requests_dict[r.idx] = r

    # list of all vehicle IDs
    monitoring = VehicleMonitoring()
    vehicle_ids = []
    no_of_parking = len(parking)
    for i in range(data.no_of_vehicles):
        pidx = i % no_of_parking
        parking_poi = parking[pidx]
        vehID = f"taxi_{i:04d}"
        sf.add_and_route_vehicle(vehID, parking_poi)
        vehicle_ids.append(vehID)
        vehicle_positions[vehID] = Vehicle(vehID=vehID)

    sumo_time = 0

    # list of passengers currently driving in vehicles
    driving = []
    un_fullfilled = []

    reservations = []

    taxi_fleet_state = TaxiFleetStateWrapper()

    timeout = int(data.epoch_timeout)
    while sumo_time < timeout:
        sumo_time = sf.simulation_step()
        full_vehicle_id_list = traci.vehicle.getIDList()
        empty_fleet = taxi_fleet_state.get_taxi_fleet(taxiState=TaxiState.Empty)

        current_reservations = traci.person.getTaxiReservations(0)
        new_reservation_ids = [r.id for r in current_reservations]
        scheduled = [r for r in reservations if r not in new_reservation_ids]
        if scheduled:
            xlog(name="scheduled", time=sumo_time, scheduled=scheduled)
        reservations = new_reservation_ids

        # monitor the distances driven
        for vehID in full_vehicle_id_list:
            if vehID in vehicle_positions:
                vehicle_positions[vehID].update()

        current_open_requests = [
            req
            for req in open_requests
            if not req.schedule_time and req.submit_time <= sumo_time + look_ahead_time
        ]
        while current_open_requests and empty_fleet:
            req = current_open_requests.pop(0)

            # find vehicle next to req.from_edge
            bestVehID = None
            min_dist = 100000
            for vehID in empty_fleet:
                vehicle_edge = vehicle_positions[vehID].edge
                stage_to = traci.simulation.findRoute(vehicle_edge, req.from_edge)
                if stage_to and len(stage_to.edges):
                    if stage_to.length < min_dist:
                        min_dist = stage_to.length
                        bestVehID = vehID
            if bestVehID:
                empty_fleet.remove(bestVehID)
                fromPoiColor = req.from_poi.color
                # set vehicle color according to POI color
                traci.vehicle.setColor(
                    vehID, (int(fromPoiColor[0]), int(fromPoiColor[1]), int(fromPoiColor[2]))
                )

                sf.dispatch(bestVehID, [req.reservation.id])
                # schedule the request --> logging
                req.schedule(vehID, sumo_time)
                monitoring.update_veh_state(vehID=vehID, state=State.to_passenger, sumo_time=sumo_time)

        left_vehicles = [
            vehID for vehID in vehicle_ids if vehID not in full_vehicle_id_list
        ]
        for vehID in left_vehicles:
            xlog(name="vehicle", time=sumo_time, vehicle=vehID, cmd="left")
            vehicle_ids.remove(vehID)

        # check entering and leaving passengers
        driving, entered, left = update_entering_and_leaving(
            driving=driving,
            open_requests=open_requests,
            vehicle_positions=vehicle_positions,
        )
        [monitoring.update_veh_state(vehID=vehID, state=State.with_passenger, sumo_time=sumo_time)
         for vehID in entered.keys()]
        [monitoring.update_veh_state(vehID=vehID, state=State.idling, sumo_time=sumo_time)
         for vehID in left.keys()]

        # check if we have fullfilled all requests
        un_fullfilled = [r for r in open_requests if r.exit_time == 0]
        if not un_fullfilled:
            sumo_time = timeout

    if Request.manager:
        d_full_mileage = 0
        for vehID, vehicle in vehicle_positions.items():
            d_full_mileage += vehicle.dist
        Request.manager.requests_finished(d_full_mileage)

    log(f"Stop at {sumo_time} with {len(un_fullfilled)} unfullfilled requests")


def sup_learn_strategy(data: ProjectConfigData):
    """
    using supervised learning to optimize dispatching
    - taxi can get in "optimizing" state (drives without passenger to strategically good position)
    - taxi can only carry one passenger

    """
    parking = data.parking
    requests = data.requests

    # add routes to sumo and store route-id in poi
    # used to initially send taxis to parking places
    for poi in parking:
        poi.route = add_route_to_poi(data.clean_edge, poi)

    vehicle_positions: Dict[Vehicle] = {}
    requests_dict = {}

    # map req.idx to requests
    for r in requests:
        r.schedule_time = None
        requests_dict[r.idx] = r

    # list of all vehicle IDs
    monitoring = VehicleMonitoring()
    vehicle_ids = []
    no_of_parking = len(parking)
    for i in range(data.no_of_vehicles):
        pidx = i % no_of_parking
        parking_poi = parking[pidx]
        vehID = f"taxi_{i:04d}"
        sf.add_and_route_vehicle(vehID, parking_poi)
        vehicle_ids.append(vehID)
        vehicle_positions[vehID] = Vehicle(vehID=vehID)

    # PRED_MODEL initialize prediction model here

    open_requests = check_requests(requests)
    sumo_time = 0

    # list of passengers currently driving in vehicles
    driving = []
    un_fullfilled = []

    taxi_fleet_state = TaxiFleetStateWrapper()

    vid_pos = {}
    for vid, veh in vehicle_positions:
        vid_pos[vid] = veh.edge
    factory = AlgorithmFactory(edge_coordinates=data.edge_coords,
                               sector_coordinates=data.sector_coords,
                               init_vehicle_pos_edges=vid_pos,
                               training_data=data.sup_learn_training_data)
    algorithm = factory.get_algorithm(algorithm_name="simple_distribution")

    timeout = int(data.epoch_timeout)
    while sumo_time < timeout:
        sumo_time = sf.simulation_step()
        full_vehicle_id_list = traci.vehicle.getIDList()
        empty_fleet = taxi_fleet_state.get_taxi_fleet(taxiState=TaxiState.Empty)

        current_reservations = traci.person.getTaxiReservations(0)
        new_reservation_ids = [r.id for r in current_reservations]
        scheduled = [r for r in reservations if r not in new_reservation_ids]
        if scheduled:
            xlog(name="scheduled", time=sumo_time, scheduled=scheduled)
        reservations = new_reservation_ids

        # monitor the distances driven
        for vehID in full_vehicle_id_list:
            if vehID in vehicle_positions:
                vehicle_positions[vehID].update()

        current_open_requests = [
            req
            for req in open_requests
            if not req.schedule_time and req.submit_time <= sumo_time
        ]
        while current_open_requests and empty_fleet:
            req = current_open_requests.pop(0)

            # find vehicle next to req.from_edge
            bestVehID = None
            min_dist = 100000
            for vehID in empty_fleet:
                vehicle_edge = vehicle_positions[vehID].edge
                stage_to = traci.simulation.findRoute(vehicle_edge, req.from_edge)
                if stage_to and len(stage_to.edges):
                    if stage_to.length < min_dist:
                        min_dist = stage_to.length
                        bestVehID = vehID
            if bestVehID:
                empty_fleet.remove(bestVehID)
                fromPoiColor = req.from_poi.color
                # set vehicle color according to POI color
                traci.vehicle.setColor(
                    bestVehID, (int(fromPoiColor[0]), int(fromPoiColor[1]), int(fromPoiColor[2]))
                )

                sf.dispatch(bestVehID, [req.reservation.id])
                # schedule the request --> logging
                req.schedule(bestVehID, sumo_time)
                monitoring.update_veh_state(vehID=bestVehID, state=State.to_passenger, sumo_time=sumo_time)
                algorithm.push_edge(vid=bestVehID, edge_id=req.from_edge, time=sumo_time)

        # PRED_MODEL if there are still unassigned vehicles, optimize their position
        for vehID in empty_fleet:
            # PRED_MODEL predict next edge
            better_pos_edge = algorithm.get_edge(vid=vehID)
            if better_pos_edge:
                # traci.vehicle.changeTarget(vehID, better_pos_edge)
                sf.route_to_edge_for_optimization(taxi_fleet_state_wrapper=taxi_fleet_state, vehID=vehID,
                                                  target_edge=better_pos_edge)

        left_vehicles = [
            vehID for vehID in vehicle_ids if vehID not in full_vehicle_id_list
        ]
        for vehID in left_vehicles:
            xlog(name="vehicle", time=sumo_time, vehicle=vehID, cmd="left")
            vehicle_ids.remove(vehID)

        # monitor the distances driven
        for vehID in full_vehicle_id_list:
            if vehID in vehicle_positions:
                vehicle_positions[vehID].update()

        # check entering and leaving passengers
        driving, entered, left = update_entering_and_leaving(
            driving=driving,
            open_requests=open_requests,
            vehicle_positions=vehicle_positions,
        )
        [monitoring.update_veh_state(vehID=vehID, state=State.with_passenger, sumo_time=sumo_time)
         for vehID in entered.keys()]
        [monitoring.update_veh_state(vehID=vehID, state=State.idling, sumo_time=sumo_time)
         for vehID in left.keys()]

        # check if we have fullfilled all requests
        un_fullfilled = [r for r in open_requests if r.exit_time == 0]
        if not un_fullfilled:
            sumo_time = timeout

    if Request.manager:
        d_full_mileage = 0
        for vehID, vehicle in vehicle_positions.items():
            d_full_mileage += vehicle.dist
        Request.manager.requests_finished(d_full_mileage)

    log(f"Stop at {sumo_time} with {len(un_fullfilled)} unfullfilled requests")