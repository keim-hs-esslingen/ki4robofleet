
  

  

# How to create requests - Example
Script path:
 `/home/steffen/projects/ki4robofleet/KI4RoboRoutingTools/Request_Creation/main.py`
Parameters:
-sd=<SUMO_DIR>  // model dir

    -sd=/home/steffen/Seattle_OSM/
-trips=<TRIPS_CSV_FILE>  // trips/taxi rides - consider Keys and format of cols of the CSV file

    -trips=/home/steffen/projects/KI4RoboRouting/Jupyter-Notebooks/seattle_trips.csv

Example of the TRIPS_CSV_FILE:

    #|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|  
    #|       | LOCATIONID | VEHICLE_VIN       | STARTED_LOCAL       | DURATION | DISTANCE | STARTLAT         | STARTLONG         | FINISHLAT        | FINISHLONG        |  
    #|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|  
    #| 1     | 21         | WMEEJ3BA1CK569248 | 2014-10-10 08:17:43 | 572      | 2        | 47.605677717487  | -122.31457969117  | 47.598724628692  | -122.32936565843  |  
    #|-------|------------|-------------------|---------------------|----------|----------|------------------|-------------------|------------------|-------------------|  

