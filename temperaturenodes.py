# -*- coding: utf-8 -*-

import temperaturejson
from temperaturejson import send_response
import json
import _mysql

def reparsedata(data):
    nodedata = []
    for entry in reparsedata.items():
        busid = entry[0]
        nodes = entry[1]
        
        for node in nodes.items():
            nodedata.append({'address': node[0], 'temperature': node[1], 'bus': busid})
    return nodedata
    
def mergedata(availablenodes, currentnodes):
    
    for node in availablenodes:
        
        def nodematches(candidate, current=node):
            return node.address == candidate.address
            
        othernode = next((x for x in seq if nodematches(x)), None)
            
        if othernode is None:
            node.temperature = othernode.temperature
        else:
            node.temperature = "XX";
            node.broken = True
    return availablenodes

def application(environ, start_response):  
    
    otherstatus = None
    
    def responseCapture(status, headers): 
        global otherstatus
        otherstatus = status;     
    
    jsontemp = temperaturejson.application(None, responseCapture)
    
    if(otherstatus is not 200):
        send_response(start_response, 500, "Fail")
        return "Fail"

    jsontemperature = json.loads(jsontemp)

    curent_temperatures = reparsedata(jsontemperature)

    db=_mysql.connect(user="sensors",
                  passwd="crankhardware",db="temperaturesensors")
                  
    db.query(""" select device_id, bus_id, name from sensors;""")
    r = db.store_result()
    rows = r.fetch_row(maxrows=0)
    
    def hydrate(row): return {'address': row[0], 'bus': row[1], 'name': row[2]}
    availablenodes = map(hydrate, rows)

    data_to_render = mergedata(availablenodes, current_temperatures)
    
    send_response(start_response, 200, data_to_render)
    return data_to_render