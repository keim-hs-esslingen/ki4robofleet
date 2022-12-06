#!/bin/bash
: '
Since SUMO 1.15.0 there was a change of the XML Schema Location
from
http://sumo.dlr.de/xsd/... 
to
https://sumo.dlr.de/xsd/...
Therefore we need to convert these Schema Locations
'
sed -i 's/http:/https:/g' *.xml
