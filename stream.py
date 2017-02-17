#!/usr/bin/env python

import socket
import Queue
import TradeData

_running = 0 

classqueue = Queue.Queue()

#connect to data stream
def connect_stream():
	host = "cs261.dcs.warwick.ac.uk"
	host_port = 80
	global _running
	_running = 1
	netcat(host, host_port, classqueue)

#disconnects from data stream
def disconnect_stream():
	global _running 
	_running = 0

def netcat(host, port, queue):
	
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	s.connect((host, int(port)))
	print("Socket connected")
	
	while (_running):
		
		data = s.recv(4096)

		if (len(data) > 0):
				data.split()
    				split_line(data, queue)

def split_line(text, queue):

    words = text.splitlines()
    count = 1

    for word in words:
        if count == 1:
        	count = 0
    		continue	
        newwords = word.split(',')
        queue.put(TradeData(newwords[0], newwords[1], newwords[2], float(newwords[3]), 
    			int(newwords[4]), newwords[5], newwords[6], newwords[7], float(newwords[8]), float(newwords[9])))

connect_stream()