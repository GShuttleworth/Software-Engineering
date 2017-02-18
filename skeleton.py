#!/usr/bin/python
import threading
import queue
import socket
import signal
import sys
import time #for testing, may need for timed reconnection

from app import app

#modules by us
from trade import *
from database import *

#global declarations and variables
_running = 0 #overall program status
_connected = 0 #connection to stream status
_q = queue.Queue() #queue for data stream
_qlock = threading.Lock() #mutex lock for queue
_threads = []
_threadID = 1

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

def manage_stream():
	global _running
	global _connected
	init_stream() #stream is a blocking method
	
	#reconnects if commanded
	while(_running):
		if(_connected):
			init_stream()

#connects to host, port
def netcat(host, port):
	try:
		#initialises socket
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	except socket.error:
		print("Failed to create socket")
	
	s.connect((host, int(port)))
	print("Stream connected")

	global _running
	global _connected
	global _q
	#TODO: filter out first line, first line is always [time,buyer,seller,price,size,currency,symbol,sector,bid,ask]
	data = s.recv(4096)
	while (_connected):
		data = s.recv(4096) #TODO: rework numbers
		if(len(data)>0):
			#puts new line of data into queue
			#print(data)
			_qlock.acquire()
			_q.put(data)
			_qlock.release()
	s.close()
	print("\nStream disconnected")

#threading
class StreamThread (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		print("Starting stream thread")
		manage_stream()

class HandlerThread (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		print("Starting event listener thread")
		self.eventListener()
	
	def eventListener(self):
		global _running
		global _qlock
		while(_running):
			#detects inputs
			try:
				#TODO actually link up mechanism to connect/disconnect
				var = input()
				if(var=='disconnect'):
					disconnect_stream()
					_qlock.acquire()
					print("Current queue size: " + str(_q.qsize()))
					_qlock.release()
				if(var=='connect'):
					connect_stream()
			except:
				break

class ProcessorThread (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
	def run(self):
		print("Starting processing thread")
		self.processing(1) #currently doing live data
	
	def processing(self,state):
		#state is processing static/live
		global _qlock
		global _running
		global _q
		#connect to db
		db = Database()
		while(_running):
			trades=self.dequeue(_q,_qlock)
			for trade in trades:
				#TODO processing here HI JAKUB
				#trade is in TradeData format (see trade.py)
				#use db.getAverage()
				#print(db.getAverage(trade.symbol))
				
				
				
				#dump to db when done
				db.addTransaction(trade)
				#TODO: update average with actual average instead of 'trade.price'
				db.updateAverage(trade.symbol, trade.price)
			
			time.sleep(2) #REMOVE AFTER TESTING, to slow down processing
		db.close()
		
	def dequeue(self,q,qlock):
		trades=[]
		data = ""
		qlock.acquire()
		if(q.qsize()>0):
			data = q.get()
		qlock.release()
		if(len(data)>0): #TODO do a better check
			#converts byte to string
			data = str(data.decode("utf-8"))
			data = data[:-2] #removes \r\n at the end, TODO what if it doesn't have \r\n?
			data = data.split('\n') #gets a list where each element is a new trade
			for x in data:
				trade = parse(x)
				trades.append(trade)
		return trades


def getdata():
	#this is for the flask application, gets data for front end
	global _q
	#data = _q.get()
	data = "lol"
	return data

#signal handling to terminate/quit
def signal_handler(signal, frame):
	global _running
	global _threads
	
	#set running states
	disconnect_stream()
	_running=0
	#rejoin threads
	for t in _threads:
		#print(t.isAlive())
		t.join()
	#print(t.isAlive())
	sys.exit()

#############################
#			main			#
#############################
@app.route('/refresh', methods=['POST'])
def refresh():
	return getdata()

def init_threads():
	#create threads
	global _threads
	global _threadID
	tstream = StreamThread(_threadID)
	tprocessor = ProcessorThread(_threadID)
	thandler = HandlerThread(_threadID)
	thandler.daemon = True
	
	tstream.start()
	_threads.append(tstream)
	_threadID += 1
	
	tprocessor.start()
	_threads.append(tprocessor)
	_threadID += 1
	
	thandler.start()
	_threads.append(thandler)
	_threadID += 1

#run web server on main thread
if __name__ == '__main__':
	_running = 1
	init_threads()
	
	#signal handler
	signal.signal(signal.SIGINT, signal_handler)
	app.run()
