# -*- coding: utf-8 -*-

from wsgiref.simple_server import make_server
from cgi import parse_qs, escape
import re
import json

import usb.core
import usb.util

def send_response(start_response, status, response_body):
        if "200" in status:
            content_type = "application/json"
        else:
            print "Returning plain text"
            content_type = "text/plain" 

        response_headers = [('Content-Type', content_type ),
                  ('Content-Length', str(len(response_body))),
                   ("Cache-Control",  "no-cache, must-revalidate")]  
                   
        start_response(status, response_headers)

# This is our application object. It could have any name,
# except when using mod_wsgi where it must be "application"
def application(environ, start_response):
    
    dev = usb.core.find(idVendor=0x04d8, idProduct=0x0f1a)
    
    if dev == None:
        status = '500 Internal Error'
        response_body = "The USB device is not plugged in!"
        send_response(start_response, status, response_body)
        return [response_body]

    else:
        cfg = dev.get_active_configuration()
        interface = cfg[(0,0)]
        in_endpoint = usb.util.find_descriptor(interface, custom_match = lambda e: 
        usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)
        out_endpoint = usb.util.find_descriptor(interface, custom_match = lambda e: 
        usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
        
        # Find out how many buses the device has/supports
        out_endpoint.write('B')
        result = "".join(map(chr, in_endpoint.read(40, timeout=500)))
        if('B' not in result):
            status = "500 Internal Server Error"
            response_body = "Inappropriate response when enumerating 1-Wire bus count: %s" % result
            send_response(start_response, status, response_body)
            return [response_body]
        
        # Scan all the 1-Wire busses
        out_endpoint.write('Q')
        result = "".join(map(chr, in_endpoint.read(40, timeout=500)))
        
        if('Q:' not in result):
            status = '500 Internal Server Error'
            response_body = 'Inappropriate response when scanning 1-Wire bus: %s' % result
            send_response(start_response, status, response_body)
            return [response_body]

        deviceCountString = re.search("Q: (.*)", result).group(1)
        
        deviceCount = map(int, deviceCountString.split(","))
        

        # Convert temperature
        out_endpoint.write('Z')            
        result = "".join(map(chr, in_endpoint.read(40, timeout=5000)))
        if(result != "ACK"):
            status = '500 Internal Server Error'
            response_body = 'Inappropriate response when calulating temperatures: %s' % result
            send_response(start_response, status, response_body)
            return [response_body]
            
        json_response = {}        
        
        for bus in range(0, len(deviceCount)):
            bus_devices = {}
            for index in range(0, deviceCount[bus]):
                out_endpoint.write("X%s,%s" % (str(bus), str(index)))
                result = "".join(map(chr, in_endpoint.read(40, timeout=500)))
                print result
                
                if "NACK" in result:
                    bus_devices.update({"Error for device %s" % str(index): result})
                    continue
                capture = re.search("X: (.*) T: (.*)", result)
                address = capture.group(1)
                temperature = capture.group(2)
                bus_devices.update({address: temperature})
            json_response[bus] = bus_devices                
        
        response_body = json.dumps(json_response)
        status = "200 OK"
        send_response(start_response, status, response_body)
        return [response_body]
        


   
if __name__ == "__main__":
   # Instantiate the WSGI server.
   
   # It will receive the request, pass it to the application
   # and send the application's response to the client
    httpd = make_server(
    'localhost', # The host name.
    8052, # A port number where to wait for the request.
    application # Our application object name, in this case a function.
    )

    # Wait for a single request, serve it and quit.
    httpd.serve_forever()
