#!/usr/bin/python

#front end imports
from flask import Flask
from flask import request, session, redirect, url_for
from werkzeug.utils import secure_filename
import json
import logging
import atexit

#processing
from datetime import datetime
import numpy as np

#modules by us
from app import mtrade
from app import database
from app import detection

#misc
import uuid #generating random session ids
import threading
import queue
import socket, errno
import signal
import sys
import time #for testing, may need for timed reconnection
import os
import csv

class databaseMode: # Used to pass info to other files
    def __init__(self, mode):
        self.mode = mode

#global declarations and variables
global _mode
_mode = 1 #1 live, 0 = static
_running = 0 #overall program status
_connected = 0 #connection to stream status
_autoconnect = 1 #if the system should try to reconnect

global dbm
dbm = databaseMode(_mode)

#Queue declarations
_q = queue.Queue() #queue for data stream
_staticq = queue.Queue() #queue for static data

#Thread declarations
_qlock = threading.Lock() #mutex lock for queue
_threads = []
_threadID = 1

#Global counters for anomaly detection
_anomalycounter = 0
_tradecounter = 0
_tradecounterlock = threading.Lock()
_tradevalue = 0

#Stores for when parsing static data
_anomalycounterstore = 0
_tradecounterstore = 0
_tradevaluestore = 0

_sessions = {} #associative array/dictionary to store all the instances of ui
_sessionslock = threading.Lock()

def init_app():
	app = Flask(__name__)
	global _running
	global _threads
	global _mode
	
	def interrupt():
		global _running
		global _threads
		#set running states
		disconnect_stream()
		_running=0
		#rejoin threads
		for t in _threads:
			#print("Thread " + t.name + " is alive: " + str(t.isAlive()))
			t.join()
			#print("Thread " + t.name + " is alive: " + str(t.isAlive()))
	
	def signal_handler(signal, frame):
		interrupt()
		sys.exit(0)
	#flask configuration
	#for sessions, generate a key instead
	
	_running=1
	#app configurations
	app.secret_key = str(uuid.uuid4())
	app.config['UPLOAD_FOLDER'] = ''
	
	load_data(_mode)
	init_threads()
	
	#on exit
	atexit.register(interrupt)
	#signal handler
	signal.signal(signal.SIGINT, signal_handler)
	return app

def load_data(mode):
	#loads data from db
	global _tradevalue
	global _tradecounter
	global _anomalycounter 
        
	dbm.mode = mode
	db = database.Database()

	_tradecounter = int(db.tradecount())
	_anomalycounter = int(db.anomalycount())
	_tradevalue = float(db.tradevalue())

	db.close()

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

def connect_stream():
	global _connected
	_connected = 1

#disconnects from data stream
def disconnect_stream():
	global _connected
	_connected = 0

class StreamThread(threading.Thread):
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
			global _qlock

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
						#raise error
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
			#debugging midnight error
			print(str(e.errno))
			#connecting if stream is down error
			if e.errno == errno.ECONNREFUSED:
				print("Stream down, aborting. Please manually reconnect")
				disconnect_stream()

class StaticFileThread(threading.Thread):
	def __init__(self,threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = "File parser thread"
	def run(self):
		print("Starting file parsing thread")
		self.prepare()
		self.parsefile()

	def prepare(self):
			#needs to clear current queue and reset counters
			global _tradecounter
			global _anomalycounter
			global _tradevalue
			global _mode
			
			disconnect_stream()

			#Resetting values
			_mode = 0
			_tradevalue = 0
			_tradecounter = 0
			_anomalycounter = 0
			print("Resetting Data")
			self.databaseReset()

	def databaseReset(self):
		global _mode
		dbm.mode = _mode
		db = database.Database()
		db.clearall(_mode)

	def parsefile(self):
			#read file
			global _qlock
			global _staticq

			print("Prepared File")

			with open('trades.csv', 'r') as csvfile:
				
				reader = csv.reader(csvfile, delimiter = ',')
		
				for row in reader:
					if row[1] == 'buyer':
						continue
					else:

						row[0] = str(row[0])
						row[1] = str(row[1]) #buyer
						row[2] = str(row[2]) #seller
						row[3] = str(row[3]) #price
						row[4] = str(row[4])
						row[5] = str(row[5])
						row[6] = str(row[6]) #symbol
						row[7] = str(row[7]) #sector
						row[8] = str(row[8])
						row[9] = str(row[9])

						_qlock.acquire()
						_staticq.put(mtrade.to_TradeData(row))
						_qlock.release()


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
		global _sessions
		
		while(_running):
			#detects inputs, remove when complete
			debug=0
			if(debug==1):
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
			#detect timers
			#TODO disconnect stream and reconnect
			#automatically reconnect
			global _mode
			global _connected
			if(_mode==1 and _connected==0 and _autoconnect==1):
				connect_stream()
				#init_threads()
			
			#TODO loop through sessions
			for key in list(_sessions): #create a copy of list as size will change due to deletion
				#see when it was last accessed, if it hasn't been accessed in the past 6 mins, delete it
				session_time = str(_sessions[key].lastAccess)
				now = str(datetime.now())
				FMT = "%Y-%m-%d %H:%M:%S.%f"
				difference = datetime.strptime(now, FMT).timestamp() - datetime.strptime(session_time, FMT).timestamp()
				#print(difference)
				if(difference>=300):
					#delete session
					global _sessionslock
					_sessionslock.acquire()
					del _sessions[key]
					_sessionslock.release()
					#print("Session ID: " + str(key) + " deleted")
			
			for i in range(30):
				if(_running):
					time.sleep(1) #wait 30 secs, no point doing every second
				else:
					break

class ProcessorThread(threading.Thread):

	stepNumOfStepsPairs = [[20, 6]]
	tickTimeCntPairs = [[0,0]]

	senstivityPerTrader = 5

	def __init__(self, threadID):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = "Data processor"

	def run(self):
		print("Starting processing thread")
		global detection
		detection = detection.Detection()

		self.processing() #currently doing live data
	
	def timeToInt(self,time):
		val = 0
		try:
			val = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f").timestamp()
		except ValueError:
			val = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").timestamp()
		return val
	
	global _numberOfRegressors
	_numberOfRegressors = 10
	
	def new_anomaly(self,db,tradeid,t,category):
		global _sessionslock
		global _anomalycounter
		global _sessions
		global _mode

		anomalyid = -1
		anomalyid = db.addAnomaly(tradeid, category, _mode)
		newAnomaly = mtrade.Anomaly(anomalyid, t, category) #todo change 3
		#doSomething with the anomaly
		_anomalycounter+=1
			#for each key in session, add this anomaly
		_sessionslock.acquire
		for key in _sessions:
			_sessions[key].put(newAnomaly)
		_sessionslock.release
	
	def refreshVals(self):
		global _tradecounter
		global _anomalycounter
		global _tradevalue
		_tradecounter = 0
		_anomalycounter = 0
		_tradevalue = 0

	def processing(self):
		#State is processing static/live
		global _qlock
		global _running
		global _q
		global _staticq
		global _mode
		it_count = 0
		previousmode = 0

		db = database.Database(_mode)
		while(_running):
			global _tradecounter
			global _tradecounterlock
			global _anomalycounter
			global _tradevalue
			
			if(previousmode!=_mode or _tradecounter==0):
				#change in mode since last iteration or if it got reset
				#reset machine learning
				detection.reset()
				if(_mode==1):
					#load from config
					#TODO
					a=1
		
			previousmode=_mode
			if (_mode == 0):
				trades = self.dequeue(_staticq, _qlock)
				it_count += 1
			else:	
				if (it_count > 0):
					it_count = 0	
					self.refreshVals()
				trades = self.dequeue(_q,_qlock)

			for t in trades:
				#Update counts
				if (not isinstance(t, mtrade.TradeData)):
					continue
				
				_tradecounter+=1 #TODO move elsewhere and mutex lock
				_tradevalue+=float(t.price)*float(t.size)
				#trade is in TradeData format (see trade.py)
				
				#dump to db
				tradeid = db.addTransaction(t, _mode)
				if(tradeid==-1):
					#error has occurred TODO insert better handler
					print("Error adding trade")
				
				# all the detection happens here
				trade_anomaly = detection.detect(t)
				
				#categorising and adding anomalies
				#key
				#1 price spike/trough
				#2 volume spike/trough
				#3 suspicious trader activity
				#calculate category
				if(len(trade_anomaly)>0):
					#add anomaly to db
					cat = -1
					if((1 in trade_anomaly) & (2 in trade_anomaly)):
						###possibly pump and dump?
						a=1
					if((2 in trade_anomaly) & (3 in trade_anomaly)):
						###insider information/bear raids?
						a=1
					if(1 in trade_anomaly):
						cat=1
					if(3 not in trade_anomaly):
						#move this out, in here for sake of testing and trader is overly sensitive
						a=1
					if(_mode == 1):
						self.new_anomaly(db,tradeid,t,cat)
					else:
						self.new_anomaly(db,tradeid,t,cat)
		
		#time.sleep(2) #REMOVE AFTER TESTING, to slow down processing
		#time.sleep(0.01) #good for cpu
		db.close()

	def dequeue(self,q,qlock):
		global _mode
		trades=[]
		data = ""
		if (_mode == 1):
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
						try:
							t = mtrade.parse(x)
							trades.append(t)
						except IndexError:
							print("Index Error") #TODO work out why it does this
		else:
			qlock.acquire()	
			if(q.qsize()>0):
				data = q.get()
			qlock.release()
			trades.append(data)
		return trades

#session stuff
class SessionData():
	def __init__(self,id):
		self.id = id
		self.queue = queue.Queue() #queue for anomalies
		self.qlock = threading.Lock()
		self.lastAccess = datetime.now()
	
	def lock(self):
		self.qlock.acquire()
	def release(self):
		self.qlock.release()
	def put(self,data):
		self.lock()
		self.queue.put(data)
		self.release()
	def get(self):
		self.lock()
		data = self.queue.get()
		self.release()
		return data
	def empty(self):
		self.updateaccess()
		self.lock()
		empty = self.queue.empty()
		self.release()
		return empty
	def updateaccess(self):
		self.lastAccess = datetime.now()

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

def getdata():
	#this is for the flask application, gets data for front end
	global _connected
	global _anomalycounter
	global _tradecounter
	global _tradevalue
	global _mode
	
	connected = False
	if(_connected==1):
		connected = True

	#puts into json format
	data = {}
	data["mode"] = _mode
	data["live"] = connected
	data["anomaly"] = _anomalycounter
	data["trades"] = _tradecounter
	data["tradevalue"] = format(_tradevalue, '.2f')

	#empty anomaly queue
	anomalies = []
	if(session.get('id') is not None):
		#print(session['id']) #debugging
		try:
			sessiondata = _sessions[session['id']]
			while not sessiondata.empty():
				x = sessiondata.get()
				#TODO
				anomaly = {}
				anomaly['id'] = x.id
				anomaly['type'] = x.category
				if(x.trade is not None):
					temp = x.trade.time.split()
					anomaly['date'] = temp[0]
					anomaly['time'] = temp[1]
					anomaly['action'] = x.trade.symbol
				anomalies.append(anomaly)
		except KeyError:
			# Key is not present, no sessions for user
			#TODO insert better handler, tell user to refresh?
			pass
	else:
		#add session
		init_session()

	data["anomalies"] = anomalies
	return json.dumps(data)

#############
app=init_app()
#view stuff here
from app import views
##########AJAX ROUTING requests###########
@app.route('/refresh', methods=['POST'])
def refresh():
	return getdata()

@app.route('/refresh_anomaly', methods=['POST'])
def refresh_anomaly():
	global _mode
	global _connected
	data = {}
	data["mode"] = _mode
	data["live"] = _connected
	return json.dumps(data)

#toggling between live and static
@app.route('/toggle', methods=['POST'])
def toggle():
	mode = int(request.json['mode'])
	global _mode
	global _connected
	if (mode==0):
		if(_connected==1):
			disconnect_stream()
		_mode=0
	if (mode==1):
		if(_connected!=1):
			connect_stream()
		else:
			return json.dumps({"change":False})
		_mode=1
	return json.dumps({"change":True})

#connect/disconnect
@app.route('/connect', methods=['POST'])
def toggleconnect():
	global _mode
	global _connected
	global _autoconnect
	if(_mode==1):
		if(_connected==1):
			disconnect_stream()
			_autoconnect=0
			return json.dumps({"change":True})
		if(_connected==0):
			connect_stream()
			_autoconnect=1
			return json.dumps({"change":True})
	return json.dumps({"change":False})

@app.route('/reset', methods=['POST'])
def resetstats():
	#for resetting current stats and db?
	global _mode
	db = database.Database()
	success=db.clearall(_mode)
	global _tradevalue
	global _tradecounter
	global _anomalycounter
	
	if(success):
		_tradevalue = 0
		_tradecounter = 0
		_anomalycounter = 0
		#reset machine learning
		return "ok"
	return "fail"
	
@app.route('/session', methods=['POST'])
def init_session():
	#check to see if a session has already been established
	id = uuid.uuid4()
	session['id'] = id
	sessiondata = SessionData(id)
	_sessions[id] = sessiondata
	return "ok"

ALLOWED_EXTENSIONS = set(['csv'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
	global _mode
	global _threads
	global _threadID
	if request.method == 'POST':
		f = request.files['file']
		if f.filename == '':
	            flash('No selected file')
	            return "not ok"
		if f and allowed_file(f.filename):
			filename = secure_filename(f.filename)
			f.save(os.path.join(app.config['UPLOAD_FOLDER'], "trades.csv"))
		else:
			print("Error with file upload")
			return "not ok"

	return "ok"

@app.route('/dismiss', methods=['POST'])
def delete_anomaly():
	global _sessions
	global _sessionslock
	anomalyid = int(request.data)
	success = 0 #update state in db
	_sessionslock.acquire
	for key in _sessions:
		if(_sessions[key]!=session['id']):
			_sessions[key].put(mtrade.Anomaly(anomalyid, None, 0))
	_sessionslock.release
	return "ok"

@app.route('/getanomalies', methods=['POST'])
def init_data():
	#get data in db
	global _mode
	db = database.Database(_mode)
	a = db.getAnomalies(0)
	#db.close()
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
	if(len(anomalies)>0):
		data["anomalies"] = anomalies
	return json.dumps(data)

@app.route('/static', methods=['POST'])
def process_static():
	global _threads
	global _threadID
	global _mode
	global _sessions
	
	#check file exists
	exists=os.path.exists("trades.csv")
	if(exists):
		_mode = 0
		
		print("Starting thread")
		tstatic = StaticFileThread(_threadID)

		tstatic.start()
		_threads.append(tstatic)
		_threadID += 1
		return "ok"
	return "fail"

@app.route('/live', methods=['POST'])
def process_live():
	global _mode
	global _sessions
	#TODO improve sessions
	if(_mode==0):
		_mode=1
		load_data(_mode)
		connect_stream()
	return "ok"
