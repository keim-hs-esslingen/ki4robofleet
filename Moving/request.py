#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# This Script provides the Class Request to store and handle Information about
# customer (passenger) requests
# =============================================================================


from Tools.XMLogger import xlog
from Tools.logger import log, elog, dlog
from Net.point_of_interest import Point_of_Interest

DEFAULT_LATENESS = 2
COST_PER_DIST = 1
VALUE_PER_DIST = COST_PER_DIST * 10


def dist_to_value(d):
    return int(d * VALUE_PER_DIST)


def dist_to_cost(d):
    return int(d * COST_PER_DIST)


MINUTE = 60


class Request:
    counter = 0
    manager = None

    def __init__(
        self,
        from_poi: Point_of_Interest,
        to_poi: Point_of_Interest,
        nid=-1,
        submit_time=0,
        calculated_distance=0,
        calculated_time=0,
    ):
        if nid >= 0:
            self.idx = nid
        else:
            self.idx = Request.counter
            Request.counter += 1
        self.person = None
        self.from_poi = from_poi
        self.to_poi = to_poi

        self.from_edge = from_poi.road
        self.to_edge = to_poi.road
        self.oldpos = from_poi.pos
        self.newpos = to_poi.pos

        # time to inform scheduler
        self.submit_time = submit_time

        # expected time to start the trip
        self.expected_start_time = self.submit_time + MINUTE * 15

        self.enter_time = 0
        self.schedule_time = None
        self.distance_at_entering = 0
        self.calculated_distance = calculated_distance
        self.calculated_time = calculated_time

        gross_tt = int(calculated_time * DEFAULT_LATENESS)
        self.expected_finish_time = self.expected_start_time + calculated_time
        self.latest_finish_time = self.expected_start_time + gross_tt

        self.contains = None
        self.path = None
        self.value = dist_to_value(calculated_distance)

        self.exit_time = 0
        self.measure = False
        assert self.oldpos >= 0.0

    def set_max_delay(self, call_to_start, realistic_time=2.0, late_time=1.25):
        # expected time to start the trip
        self.expected_start_time = self.submit_time + call_to_start

        # calc. maximum tolerable delay
        gross_tt = int(self.calculated_time * realistic_time)
        later_tt = int(gross_tt * late_time)
        self.expected_finish_time = self.expected_start_time + gross_tt
        self.latest_finish_time = self.expected_start_time + later_tt

    def reset(self):
        self.enter_time = 0
        self.exit_time = 0
        self.schedule_time = 0
        self.reservation = None

    def new_idx(self):
        Request.counter += 1
        self.idx = Request.counter

    def set_person(self, p):
        assert self.person == None
        self.person = p

    def to_str(self):
        return f"{self.idx}: init: {self.submit_time}, enter:{self.enter_time}, exit: {self.exit_time}"

    def schedule(self, v, t):
        if not self.schedule_time:
            self.schedule_time = t
            if self.measure:
                xlog(
                    name="request",
                    time=t,
                    vehicle=v,
                    cmd="schedule",
                    req_id=self.idx,
                    submit_time=self.submit_time,
                )
        else:
            xlog(
                name="request_error",
                time=t,
                vehicle=v,
                req_id=self.idx,
                schedule_time=self.schedule_time,
            )

    def enter(self, v, t, d):
        self.enter_time = t
        self.distance_at_entering = d
        self.vehID = v

        # current time - expected time of start
        t_late = t - self.expected_start_time

        if self.measure:
            xlog(
                name="request",
                time=t,
                vehicle=v,
                cmd="enter",
                req_id=self.idx,
                distance=f"{d:.3f}",
                t_late=t_late,
            )

    def leave(self, t, d_full_mileage):
        self.exit_time = t
        t_wait = max(0, self.enter_time - self.submit_time)
        t_drive = t - self.enter_time

        t_late = max(0, t - self.latest_finish_time)  # t > latest ?
        t_early = min(0, t - self.expected_finish_time)  # t < finish ?
        d_pass = d_full_mileage - self.distance_at_entering

        if self.measure:
            if Request.manager:
                Request.manager.request_finished(
                    t_wait, t_drive, d_full_mileage, d_pass
                )
            dlog(
                f"Req {self.idx:02d} leaves {self.vehID} after {t:4d} - {self.enter_time:4d} = {t - self.enter_time}"
            )

            t_est = float(self.expected_finish_time - self.expected_start_time) / float(
                self.exit_time - self.enter_time
            )
            xlog(
                name="request",
                time=t,
                vehicle=self.vehID,
                cmd="finished",
                req_id=self.idx,
                dist_w_psg=f"{d_pass:.3f}",
                t_submit=self.submit_time,
                t_schedule=self.schedule_time,
                t_enter=self.enter_time,
                t_finish=self.expected_finish_time,
                t_latest=self.latest_finish_time,
                t_drive=t_drive,
                t_est=f"{t_est:.1f}",
                t_late=t_late,
                t_early=t_early,
            )

    def __str__(self):
        return "q_{:04d}".format(self.idx)
