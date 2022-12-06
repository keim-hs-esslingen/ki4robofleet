# This is a small script to test the usage and behavior of the TraCI Taxi Dispatch algorithm

import os, sys

import traci 

# this is the normal SUMO start with TraCI
sumoCmd = ["sumo-gui", "-c", "osm.sumocfg"]
traci.start(sumoCmd)

# to use the TraCI Taxi Dispatch algorithm some additional parameters need to be loaded
sumoStart = [
    "-S",
    "--device.taxi.dispatch-algorithm",
    "traci",
    "-c",
    "osm.sumocfg",
]
traci.load(sumoStart)

# Hint: IDs must be Strings and not Integer
# otherwise an Error like "TypeError: object of type 'int' has no len()" arises
 
# To add a vehicle, we must create an arbitrary initial Route
initialVehicleRoute = traci.simulation.findRoute("564727794","155186281")

# add Route to TraCI
traci.route.add("myInitialRoute_1", initialVehicleRoute.edges)

# add a Taxi to TraCI
traci.vehicle.add("myTaxi_1", "myInitialRoute_1", typeID="taxi", line="taxi")

# add a Taxi Customer 1
traci.person.add("myTaxiCustomer_1", "432904391#0", 1, typeID='DEFAULT_PEDTYPE')
# adding Taxi Reservation for Taxi Customer 1
traci.person.appendDrivingStage("myTaxiCustomer_1","-24181299#0", lines="taxi")

# add a Taxi Customer 2
traci.person.add("myTaxiCustomer_2", "332731760#0", 1, typeID='DEFAULT_PEDTYPE')
# adding Taxi Reservation for Taxi Customer 2
traci.person.appendDrivingStage("myTaxiCustomer_2","-22701320#3", lines="taxi")


i = 0

# to see the reservation list, the first Simulationstep has to be performed
traci.simulation.step()
reservations = traci.person.getTaxiReservations(0)
print("Current Taxi Reservations: ")
for r in reservations:
    print(r)

# for Taxi dispatching we need the IDs of the Reservations
reservation_ids = [r.id for r in reservations]
print("Current Taxi Reservation IDs")
print(reservation_ids)

# Now we can set the order in which the Reservations are processed
# In our case Taxi Customer 2 is picker up first and then Taxi Customer 1
traci.vehicle.dispatchTaxi("myTaxi_1", reservation_ids[1])
traci.vehicle.dispatchTaxi("myTaxi_1", reservation_ids[0])

# Now we perform the Simulation
while i < 1200:
    traci.simulation.step()
    i = i+1    












