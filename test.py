#!/usr/bin/python
import threading
import socket

#global declarations
_running = 0 #overall program status
_connected = 0 #connection to stream status

#connect to data stream
def init_stream():
	host = "cs261.dcs.warwick.ac.uk"
	host_port = 80
	connect_stream()
	netcat(host, host_port)

def connect_stream():
	global _connected 
	_connected = 1

#disconnects from data stream
def disconnect_stream():
	global _connected 
	_connected = 0

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
	
	global _running
	global _connected
	while(_running):
		while (_connected):
			data = s.recv(4096);
			if(len(data)>0):
				#todo
				#each line begins with b' and ends with '
				print(data) #stick data in a queue obv


#threading
class myThread (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		print("Starting thread")
		init_stream()


#main
_running = 1
#create threads
thread1 = myThread(1)

#start threads
thread1.start()

while(_running):
	var = input("Please enter something: ")
	if(var=='d'):
		disconnect_stream()
	if(var=='c'):
		connect_stream()
