#!/usr/bin/python
import threading
import queue
import socket
import signal
import sys
import time #for testing, may need for timed reconnection
from datetime import datetime

import numpy as np

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
	print("Stream disconnected")

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
		eventListener()

def eventListener():
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


		setupCompanyData() #setup comapny data, one-off at the beginning


		processing(1) #currently doing live data

def dequeue():
	global _qlock
	global _running
	trades=[]
	data = ""
	_qlock.acquire()
	if(_q.qsize()>0):
		data = _q.get()
	_qlock.release()
	if(len(data)>0): #TODO do a better check
		#converts byte to string
		data = str(data.decode("utf-8"))
		data = data[:-2] #removes \r\n at the end, TODO what if it doesn't have \r\n?
		data = data.split('\n') #gets a list where each element is a new trade
		for x in data:
			trade = parse(x)
			trades.append(trade)
	return trades


#Jakub here, this might be expanded/changed/moved out later
class StockData:
	#contains company symbol, polynomial coefficients for best fit line and range within it's considered not anomolalous
	def __init__(self, symbol, coeffList, rangeVal):
		self.symbol = symbol
		self.coeffList = coeffList
		self.range = rangeVal
		self.currCnt = 0
		self.xVals = np.empty(2)
		self.yVals = np.empty(2)
	
	#compare actual vs predicted value
	def detectError(x, y):
		return (y>=(x*self.coeffList[0]+self.coeffList[1])*(1+self.rangeVal) or 
				y<=(x*self.coeffList[0]+self.coeffList[1])*(1-self.rangeVal))	

	def updateCoeffs():
		print(self.coeffList)
		self.coeffList = np.polyfit(listX, listY, 1)
		print(self.coeffList)

def setupCompanyData():	

	#to chagne in the future
	global blndl


	#create just for one company for now
	tempCoeffs = [0.0, 0.0]
	rangeVal = 0.2
	blndl = StockData("BLND.L", tempCoeffs, rangeVal)
	print("blndl setup")


def timeToInt(time):
	return datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f").timestamp()


def processing(state):
	#state is processing static/live
	#connect to db
	db = Database()
	while(_running):
		trades=dequeue()
		for trade in trades:
			#TODO processing here HI JAKUB
			#trade is in TradeData format (see trade.py)
			#use db.getAverage()
			#print(db.getAverage(trade.symbol))
			
			#done for one company for now
			print ("dequeuing")
			if (trade.symbol != "BLND.L"):
				break

			print(timeToInt(trade.time), trade.price)
			print("found")
			blndl.xVals[blndl.currCnt]=timeToInt(trade.time)
			blndl.yVals[blndl.currCnt]=trade.price


			blndl.currCnt += 1
			print(blndl.currCnt)

			if (blndl.currCnt == 2):
				blndl.updateCoeffs
				print (blndl.coeffList)
				blndl.currCnt = 0


			#dump to db when done
			#db.addTransaction(trade) 
			#TODO: update average with actual average instead of 'trade.price'
			#db.updateAverage(trade.symbol, trade.price)

		time.sleep(2) #REMOVE AFTER TESTING, to slow down processing
	db.close()


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
