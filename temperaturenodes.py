# -*- coding: utf-8 -*-


import os
import sys

sys.path.append(os.path.dirname(__file__))

import temperaturejson
from temperaturejson import send_response
import json
import _mysql

def reparsedata(data):
    nodedata = []
    for entry in data.items():
        busid = entry[0]
        nodes = entry[1]
        
        for node in nodes.items():
            nodedata.append({'address': node[0], 'temperature': node[1], 'bus': busid})
    return nodedata
    
def mergedata(databasenodes, currentnodes):
    for node in databasenodes:
        
        def nodematches(candidate, current=node):
            return current['address'] == candidate['address']
            
        othernode = next((x for x in currentnodes if nodematches(x)), None)
            
        if othernode is not None:
            print othernode
            node['temperature'] = othernode['temperature']
        else:
            node['temperature'] = "XX";
            node['broken'] = True
    return databasenodes

def application(environ, start_response):  
    global otherstatus
    otherstatus = None
    
    def responseCapture(status, headers): 
        global otherstatus
        otherstatus = status;     
    
    jsontemp = temperaturejson.application(None, responseCapture)[0]
    
    if("200" not in otherstatus):
        send_response(start_response, "500 Internal Server Error", jsontemp)
        return [jsontemp]

    jsontemperature = json.loads(jsontemp)

    current_temperatures = reparsedata(jsontemperature)

    db=_mysql.connect(user="sensors",
                  passwd="crankhardware",db="temperaturesensors")
                  
    db.query(""" select device_id, bus_id, name from sensors;""")
    r = db.store_result()
    rows = r.fetch_row(maxrows=0)
    
    def hydrate(row): return {'address': row[0], 'bus': row[1], 'name': row[2]}
    databasenodes = map(hydrate, rows)

    data_to_render = mergedata(databasenodes, current_temperatures)

    stringresult = json.dumps(data_to_render, sort_keys=True, indent=4, separators=(',', ': '))    
    send_response(start_response, "200 OK", stringresult)
    return [stringresult]
