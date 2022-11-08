import datetime as dt

import lxml.etree as ET
import pandas as pd
import traci 


print("Converting historical Taxi-Ride GeoData to CustomerRequest.xml ... ")

# preparing tree - structure of the CustomerRequest.xml
xml_output = ET.Element("requestlist")
requestId = 0

# starting SUMO
sumoCmd = ["sumo-gui", "-c", "./NYC_TestModel/osm.sumocfg"]
traci.start(sumoCmd)

# df is a DataFrame
df = pd.read_csv('GeoPosTestData.csv')
# print all lines
for index, row in df.iterrows():
    
    # reading and formatting Pickup- Date and Time
    # this is a bit tricky, because you havee to type %I  
    pickupTime = dt.datetime.strptime(row['lpep_pickup_datetime'], "%d/%m/%Y %I:%M:%S %p")
   
    # we assume to consider just one day for the simulation and we convert the time to seconds of the current day 
    submitTime = int(pickupTime.timestamp()-pickupTime.replace(hour=0, minute=0, second=0).timestamp())

    pickUpLongitude = row['Pickup_longitude']
    pickUpLatitude = row['Pickup_latitude']

    dropOffLongitude = row['Dropoff_longitude']
    dropOffLatitude = row['Dropoff_latitude']

    try:
        # converting Geo Position to SUMO Edge
        (pickUpedgeID,pickUpEdgePosition,pickUpLaneIndex) = traci.simulation.convertRoad(float(pickUpLongitude), float(pickUpLatitude), True, vClass="taxi")   
        (dropOffedgeID,dropOffEdgePosition,dropOffLaneIndex) = traci.simulation.convertRoad(float(dropOffLongitude), float(dropOffLatitude), True, vClass="taxi")   

        print("------------ Row Index:",index,"Reqest Id:",requestId,",Submit Time:",submitTime,"(",pickupTime,") ------------")
        print("pickup at lon:", pickUpLongitude, "lat:", pickUpLatitude, "-> Edge Id:",pickUpedgeID, " Pos:",pickUpEdgePosition, "Lane:",pickUpLaneIndex)
        print("dropoff at lon:", dropOffLongitude, "lat:", dropOffLatitude ,"-> Edge Id:",dropOffedgeID, " Pos:",dropOffEdgePosition, "Lane:",dropOffLaneIndex)

        #writing line to xml file
        ET.SubElement(xml_output,"request",
                        id=str(requestId),
                        submitTime=str(submitTime),
                        fromEdge=pickUpedgeID,
                        fromEdgePosition="{:.2f}".format(pickUpEdgePosition),
                        toEdge=dropOffedgeID,
                        toEdgePosition="{:.2f}".format(dropOffEdgePosition)
                    )
        requestId += 1
    except:
        print("ERROR: The Positions at Row Index",index,"could not be converted")

# formatting and writing the CustomerRequest.xml  
tree = ET.ElementTree(xml_output)
tree.write(
    "./CustomerRequests.xml",
    encoding="UTF-8",
    xml_declaration=True,
    pretty_print=True,
)
print("\nREADY! CustomerRequests.xml was created")









