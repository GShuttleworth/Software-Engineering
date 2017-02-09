#!/usr/bin/python
import threading
import socket

#global declarations
_running = 0

#connect to data stream
def connect_server():
	host = "cs261.dcs.warwick.ac.uk"
	host_port = 80
	global _running 
	_running = 1
	netcat(host, host_port)

#disconnects from data stream
def disconnect_server():
	global _running 
	_running = 0


#connects to host, port
def netcat(host, port):
	try:
		#initialises socket
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error:
		print("Failed to create socket")

	s.connect((host, int(port)))
	print("Socket connected")
	#filter out first line, first line is always [time,buyer,seller,price,size,currency,symbol,sector,bid,ask]
	
	global global_running
	while (_running):
		data = s.recv(4096);
		if(len(data)>0):
			#todo
			#each line begins with b' and ends with '
			print(data)


#

#main
connect_server()
