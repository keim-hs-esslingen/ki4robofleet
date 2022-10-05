#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: andreas.roessler@hs-esslingen.de
# Date: May 2021
# License: MIT License
# =============================================================================
# This Script is the Entrypoint for the SUMO Simulation after the Model is ready
# The name web_taxi_runner indicates, that the Simulation can be performed eiter
# on the local machine or on a remote machine (e.g. high performance cluster).
# To perform the Simulation, a bunch of paramters is required.
# =============================================================================

# usage example: python3 ./web_taxi_runner.py -f ./MannheimBig-Morning/CustomerRequests.xml -c ./MannheimBig-Morning/osm.sumocfg -t 3600 -e 45085545 -s "simple, look_ahead, shared" -n "10" -a 900 -r "1.0" -l "1.0"

from Web.server import WebServer
import os
import optparse
import datetime
from datetime import datetime
from pathlib import Path
from Moving.request_manager import Request_Manager
from Project.project import Project
from Project.project_data import ProjectConfigData, project_config_from_options
from Tools.logger import log, elog
from Tools.XMLogger import write_log
from Tools.json_io import write_JSON

import sys

sys.setrecursionlimit(1500)

MINUTE = 60

dir = os.path.dirname(__file__)

mtime = os.path.getmtime(__file__)
dt_mtime = datetime.fromtimestamp(mtime)
mtime_string = dt_mtime.strftime("%Y-%m-%d %H:%M:%S")


# Default input parameters can be defined here:
data_set = "MannheimMorningScenario"
requests_file = os.path.abspath(os.path.join(dir, data_set, "CustomerRequests.xml"))

# If the Simulation is performed many times, using a pickle file speeds up the Simulation, because the initial Steps can be skipped:
project_file = os.path.abspath(os.path.join(dir, data_set, "morning_web.pickle"))

# the sumo_config_file is an xml file containing all data which are read by SUMO
sumo_config_file = os.path.abspath(os.path.join(dir, data_set, "osm.sumocfg"))

# All Simulation- Results will be collected into this directory
results_dir = os.path.join(dir, "Results")
Path(results_dir).mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ws = WebServer()
    # a dict to be delivered by web server
    sumo_public = {}
    sumo_public["main file modified"] = mtime_string
    ws.dynamic["/sumo"] = sumo_public
    Request_Manager(sumo_public=sumo_public)

    # The Simulation Input Files and Parameters are read with OptionParser which will overwrite the default paramters:
    parser = optparse.OptionParser()
    parser.add_option(
        "-a",
        "--look_ahead_time",
        action="store",
        dest="look_ahead_time",
        help="look ahead time in secs; default 1 hour = 3600",
        default="3600",
    )
    parser.add_option(
        "-c",
        "--config",
        action="store",
        dest="sumo_config_file",
        help="SUMO config file to load",
        default=sumo_config_file,
    )
    parser.add_option(
        "-e",
        "--cleanedge",
        action="store",
        dest="clean_edge",
        help="edged to start the cleaning process",
        default="45085545",
    )
    parser.add_option(
        "-f",
        "--requests_file",
        action="store",
        dest="requests_file",
        help="requests file to load",
        default=requests_file,
    )

    parser.add_option(
        "-g",
        "--show_gui",
        action="store",
        dest="show_gui",
        help="show SUMO GUI during the Simulation",
        default="True",
    )

    parser.add_option(
        "-l",
        "--lateness_factors",
        action="store",
        dest="lateness_factors",
        help="exepected_finish = travel_time * lateness_factor",
        default="1.0, 1.1",
    )
    parser.add_option(
        "-n",
        "--num_veh_list",
        action="store",
        dest="num_veh_list",
        help="simulated num of vehicles as list [5,10,15]",
        default="50, 100",
    )
    parser.add_option(
        "-p",
        "--project",
        action="store",
        dest="project_file",
        help="project/pickle-file to load",
        default=project_file,
    )
    parser.add_option(
        "-r",
        "--realistic_times",
        action="store",
        dest="realistic_times",
        help="travel_time = sumo_estimate * realistic_time",
        default="2.0",
    )
    # List with Strategies
    parser.add_option(
        "-s",
        "--strategies",
        action="store",
        dest="strategy_list",
        help="strategy used",
        default="simple",
    )
    parser.add_option(
        "-t",
        "--epoch_timeout",
        action="store",
        dest="epoch_timeout",
        help="time out in secs; default 1 hour = 3600",
        default="36000",
    )

    options, args = parser.parse_args()
    config: ProjectConfigData = project_config_from_options(options)

    # convert to int
    string_list = options.num_veh_list.split(",")
    NUM_OF_VEHICLES = [int(s) for s in string_list]

    # convert to float
    string_list = options.realistic_times.split(",")
    REALISTIC_TIMES = [float(s) for s in string_list]

    # convert to float
    string_list = options.lateness_factors.split(",")
    LATENESS_FACTORS = [float(s) for s in string_list]

    # remove leading/trailing spaces
    string_list = options.strategy_list.split(",")
    strategy_list = [s.strip() for s in string_list]

    p = Project()
    p.load(config=config)
    results = []

    # gross_travel_time = net_travel_time * realistic_time
    # latest arrival time = start_time + gross_travel_time * late_time

    # here the simulation loops over all strategies and parameters are performed:
    for strategy in strategy_list:
        if strategy != "shared":
            for n in NUM_OF_VEHICLES:
                p.set_max_delay(
                    call_to_start=MINUTE * 15, realistic_time=1.0, late_time=1.0
                )
                elog("#####################################################")
                elog(f'Starting "{strategy}" strategy with {n} vehicles')
                p.data.no_of_vehicles = n
                startTime = datetime.now()
                result = p.run_requests(strategy=strategy)
                endTime = datetime.now()
                cpuTime = int((endTime - startTime).total_seconds())
                if result:
                    result["cpuTime (sec)"] = cpuTime
                    results.append(result)
                now = datetime.now()
                write_log(
                    os.path.abspath(
                        os.path.join(
                            results_dir, now.strftime("epoch_%Y_%m_%d-%H_%M.xml")
                        )
                    )
                )
        else:
            for realistic_time in REALISTIC_TIMES:
                for lateness_factor in LATENESS_FACTORS:
                    p.set_max_delay(
                        call_to_start=MINUTE * 15,
                        realistic_time=realistic_time,
                        late_time=lateness_factor,
                    )
                    p.calc_shared(realistic_time=realistic_time)
                    elog("#####################################################")
                    elog(f'Starting "{strategy}"')
                    elog(
                        f"realistic_time {realistic_time} lateness_factor {lateness_factor}"
                    )
                    p.data.no_of_vehicles = 1
                    startTime = datetime.now()
                    result = p.run_requests(strategy=strategy)
                    endTime = datetime.now()
                    cpuTime = int((endTime - startTime).total_seconds())
                    if result:
                        result["cpuTime (sec)"] = cpuTime
                        result["realistic_time"] = realistic_time
                        result["lateness_factor"] = lateness_factor
                        results.append(result)
                    now = datetime.now()
                    write_log(
                        os.path.abspath(
                            os.path.join(
                                results_dir, now.strftime("epoch_%Y_%m_%d-%H_%M.xml")
                            )
                        )
                    )

        # write session
        session = {
            "request_file": options.requests_file,
            "sumo_config_file": options.sumo_config_file,
        }
    filename = os.path.abspath(
        os.path.join(results_dir, now.strftime("session_%Y_%m_%d-%H_%M.json"))
    )
    write_JSON(filename, {"session": session, "results": results})
    log(f"written results to <{filename}>")
