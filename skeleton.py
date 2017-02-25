#!/usr/bin/python
import threading
import queue
import socket, errno
import signal
import sys
import time #for testing, may need for timed reconnection

#processing
from datetime import datetime
import numpy as np

#front end imports
import json
from app import app
import logging

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

_anomalyq = queue.Queue()
_anomalyqlock = threading.Lock()
_anomalycounter = 0
_tradecounter = 0
_tradecounterlock = threading.Lock()
_tradevalue = 0

def connect_stream():
	global _connected
	_connected = 1

#disconnects from data stream
def disconnect_stream():
	global _connected
	_connected = 0

#threading
class StreamThread (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = "Data stream"
	def run(self):
		print("Starting stream thread")
		self.manage_stream()
	
	#connect to data stream
	def init_stream(self):
		host = "cs261.dcs.warwick.ac.uk"
		host_port = 80
		connect_stream()
		self.netcat(host, host_port)
	
	def manage_stream(self):
		global _running
		global _connected
		self.init_stream() #stream is a blocking method
		
		#reconnects if commanded
		while(_running):
			if(_connected):
				self.init_stream()

	#connects to host, port
	def netcat(self, host, port):
		try:
			#initialises socket
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error:
			print("Failed to create socket")
		
		try:
			s.connect((host, int(port)))
			print("Stream connected")

			global _running
			global _connected
			global _q
			#TODO: filter out first line, first line is always [time,buyer,seller,price,size,currency,symbol,sector,bid,ask]
			data = s.recv(4096)
			counter=0 #a counter to see how many iterations of no data
			while (_connected):
				s.settimeout(2) #if no data comes in, s.recv becomes blocking
				try:
					data = s.recv(4096) #TODO: rework numbers
				except socket.timeout as e:
					if(counter>60):
						print("No data received in the past 2 minutes. Disconnecting stream")
						disconnect_stream()
					counter+=1
				else:
					if(len(data)>0):
						#puts new line of data into queue
						_qlock.acquire()
						_q.put(data)
						_qlock.release()
					counter=0
			s.close()
			print("\nStream disconnected")
			
		except socket.error as e:
			if e.errno == errno.ECONNREFUSED:
				print("Stream down, aborting. Please manually reconnect")
				disconnect_stream()

class HandlerThread (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = "Handler"
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

class StockData:
	#contains company symbol, polynomial coefficients for best fit line and range within it's considered not anomolalous
	def __init__(self, symbol, coeffList, rangeVal):
		self.symbol = symbol
		self.coeffList = coeffList
		self.range = rangeVal
		self.currCnt = 0
		self.xVals = np.empty(_numberOfRegressors)
		self.yVals = np.empty(_numberOfRegressors)

	#compare actual vs predicted value
	def detectError(x, y):
		return (y>=(x*self.coeffList[0]+self.coeffList[1])*(1+self.rangeVal) or 
			y<=(x*self.coeffList[0]+self.coeffList[1])*(1-self.rangeVal)) 

	def updateCoeffs(self):
		self.coeffList = np.polyfit(self.xVals, self.yVals, 1)


class ProcessorThread (threading.Thread):
	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = "Data processor"
	def run(self):
		print("Starting processing thread")

		#setup comapny data, one-off at the beginning
		global companyList
		companyList = {}
		#some process to load data from db
		
		self.processing(1) #currently doing live data

	#Jakub here, this might be expanded/changed/moved out later

	def setupCompanyData(self,trade):
		#create just for one company for now
		tempCoeffs = [0.0, 0.0]
		rangeVal = 0.2
		companyList[trade.symbol] = StockData(trade.symbol, tempCoeffs, rangeVal)
		#print(trade.symbol, " setup") #debugging


	def timeToInt(self,time):
		return datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f").timestamp()

	global _numberOfRegressors
	_numberOfRegressors = 3
	
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
				#update counts
				global _tradecounter
				global _tradecounterlock
				global _anomalycounter
				global _tradevalue
				
				_tradecounter+=1 #TODO move elsewhere and mutex lock
				_tradevalue+=float(trade.price)+float(trade.size)
				#trade is in TradeData format (see trade.py)
				#use db.getAverage()
				#print(db.getAverage(trade.symbol))
				
				# print ("dequeuing") #debugging
				symb = trade.symbol 

				#create a StockData objecty for every coimap0ny
				if (symb not in companyList):
					self.setupCompanyData(trade)

				# print(symb, timeToInt(trade.time), trade.price) #debugging

				#update keep a buffer of _num_of_regressors recent avlues for regressipn
				companyList[symb].xVals[companyList[symb].currCnt]=self.timeToInt(trade.time)
				companyList[symb].yVals[companyList[symb].currCnt]=trade.price
				
				
				if(np.all(companyList[symb].coeffList != [0.0, 0.0])):
					# print(companyList[symb].coeffList) #debugging
					if(companyList[symb].detectError(self.timeToInt(trade.time), float(trade.price))):
						print("error") #debugging
						# newAnomaly = Anomaly(1, trade, "price per company")
						#doSomething with the anomaly

					else:
						print("not error") #debugging


				companyList[symb].currCnt += 1
				# print(companyList[symb].currCnt) #debugging

				#every sewveral bvvalues, the line fit is updated (prevents consttant updates)
				if (companyList[symb].currCnt == _numberOfRegressors):
					companyList[symb].updateCoeffs()
					# print (companyList[symb].coeffList) #debugging
					companyList[symb].currCnt = 0


				#dump to db when done
				db.addTransaction(trade)
				#TODO: update average with actual average instead of 'trade.price'
				#db.updateAverage(trade.symbol, trade.price)
			
			#time.sleep(2) #REMOVE AFTER TESTING, to slow down processing
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

#signal handling to terminate/quit
def signal_handler(signal, frame):
	global _running
	global _threads
	
	#set running states
	disconnect_stream()
	_running=0
	#rejoin threads
	for t in _threads:
		#print("Thread " + t.name + " is alive: " + str(t.isAlive()))
		t.join()
		#print(t.isAlive())
	sys.exit()

#############################
#			main			#
#############################
##########AJAX ROUTING requests###########
@app.route('/refresh', methods=['POST'])
def refresh():
	return getdata()

@app.route('/getanomalies', methods=['POST'])
def init_data():
	#get data in db
	db = Database()
	a = db.getAnomalies(0)
	db.close()
	data = {}
	#TODO
	anomalies = []
	for x in a:
		temp = x.trade.time.split()
		anomaly = {}
		anomaly['id'] = x.id
		anomaly['type'] = x.category
		anomaly['date'] = temp[0]
		anomaly['time'] = temp[1]
		anomaly['action'] = x.trade.symbol
		anomalies.append(anomaly)
	#make into json
	data["anomalies"] = anomalies
	return json.dumps(data)

def getdata():
	#this is for the flask application, gets data for front end
	global _connected
	global _anomalycounter
	global _tradecounter
	global _tradevalue
	
	connected = False
	if(_connected==1):
		connected = True

	#puts into json format
	data = {}
	data["live"] = connected
	data["anomaly"] = _anomalycounter
	data["trades"] = _tradecounter
	data["tradevalue"] = format(_tradevalue, '.2f')

	#empty anomaly queue
	anomalies=[]
	data["anomalies"] = anomalies
	return json.dumps(data)

############################## MAIN
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
	#only show errors in console, needs logging import
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)
	
	_running = 1
	init_threads()
	
	#help
	print("\t\t\t****Use CTRL+C then Enter key to exit****")
	print("\t\t\t\tFlask logging mode off\n")
	
	#signal handler
	signal.signal(signal.SIGINT, signal_handler)
	app.run()
