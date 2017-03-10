import numpy as np
from datetime import datetime

def test(counter):
	global _anomalycounter
	counter+=1
	_anomalycounter+=1
	return

# DETECTION MODULE:	

class Detection:

	def returnJson(self):
		return json.dumps( (companyList, traderList) )

	def restoreFromJson(self, json):
		dump = json.dumps(json)
		self.companyList = dump[0]
		self.traderList = dump[1]
		self.numOfStepVariants = len(self.stepLength)

	stepLength = [120, 400]	#each pair represents a pair of step length (in seconds)
	# and the number of steps between line fit update
	currTime = [0]	# keeps track of the start time of the current step cycle
	# the number of steps that have already happened

	# how many times more valuable a trade has to be than an average value of a trader to raise an error
	senstivityPerTrader = 7.3
	volumeSensitivity = 6
	frequencySensitivity = 5.5
	minTraderTrades = 5

	# linear regression of price for this many trades per company
	numberOfRegressors = 20

	def __init__(self):	
		self.companyList = {}
		self.traderList = {}
		# self.sectorList = {}
		self.numOfStepVariants = len(self.stepLength)


	def reset(self):		
		#setup company data, one-off at the beginning
		self.companyList = {}
		#some process to load data from db
		self.numOfStepVariants = len(self.stepLength)
		#rolling average for all traders
		#(exponential moving average should make it very computationally efficient)
		self.traderList = {}
		#rolling average for all sectors
		#(exponential moving average should make it very computationally efficient)
		# self.sectorList = {}
		

	def setupCompanyData(self, t):
		self.companyList[t.symbol] = StockData(t.symbol, self.stepLength, self.numberOfRegressors)
		#Set the time for the first trade
		for x in range(self.numOfStepVariants):
			self.companyList[t.symbol].currTime[x] = (int(timeToInt(t.time)/self.stepLength[x]))*self.stepLength[x] #rounds down to to the nearest step	

					
		

	def detect(self, t):
		#######
		#anomalies
		trade_anomaly = []

		symb = t.symbol

		# create a StockData object for every company
		if (symb not in self.companyList):
			self.setupCompanyData(t)
			# trade_anomaly.append(1)
				
		#	PRICE REGRESSION


		self.companyList[symb].priceRegression.addTrade(t)

		if(np.all(self.companyList[symb].priceRegression.coeffList != [0.0, 0.0])):
			# print(self.companyList[symb].priceCoeffList) #debugging
			if(self.companyList[symb].priceRegression.detectError(timeToInt(t.time), float(t.price)) and
				self.companyList[symb].priceRegression.notdetected):
				print("price anomaly for x = ", timeToInt(t.time), " y = ", float(t.price)) #debugging
				print("expected x = ", timeToInt(t.time), " y = ", self.companyList[symb].priceRegression.coeffList[0]*timeToInt(t.time) + self.companyList[symb].priceRegression.coeffList[1]) #debugging
				#add price anomaly to category
			# else:
			# 	print("no price anomaly for x = ", timeToInt(t.time), " y = ", float(t.price)) #debugging
			# 	print("expected x = ", timeToInt(t.time), " y = ", self.companyList[symb].priceRegression.coeffList[0]*timeToInt(t.time) + self.companyList[symb].priceRegression.coeffList[1]) #debugging
				trade_anomaly.append(1)
				self.companyList[symb].priceRegression.notdetected = False


		#
		#	FREQUENCY AND VOLUME REGRESSION
		#

		for x in range(len(self.stepLength)): #for every possible tick length/beginning time
			if(timeToInt(t.time) >= self.stepLength[x]+self.companyList[symb].currTime[x]): #if the current tick has expired

				# get volume/frequency total for the lest unit of time
				lastFreq = float(self.companyList[symb].frequencyRegression[x])
				lastVol = float(self.companyList[symb].volumeRegression[x])

				#if a minimum numbers of passes required to generate a prediction has passed return an anomlay if detected
				if(self.companyList[symb].currCnt[x]>10):
					if(self.detectError(lastFreq, self.companyList[symb].frequencyAvg, self.frequencySensitivity, self.frequencySensitivity/3)):
						print("freq error for ", lastFreq, " expected ", self.companyList[symb].frequencyAvg)
						trade_anomaly.append(4)
					
					if(self.detectError(lastVol, self.companyList[symb].volumeAvg, self.volumeSensitivity, self.volumeSensitivity/3)):
						print("vol error for ", lastVol, " expected ", self.companyList[symb].volumeAvg)
						trade_anomaly.append(2)
				else:
					self.companyList[symb].currCnt[x] += 1

				self.companyList[symb].currTime[x] += self.stepLength[x]

				#if the volume and frequency average already have been assigned a value
				if(self.companyList[symb].volumeAvg>0):
					#run exponential moving average
					self.companyList[symb].volumeAvg = self.companyList[symb].volumeAvg*0.8 + lastVol*0.2
					self.companyList[symb].frequencyAvg = self.companyList[symb].frequencyAvg*0.8 + lastFreq*0.2
				else:
					self.companyList[symb].volumeAvg = lastVol
					self.companyList[symb].frequencyAvg = lastFreq

				self.companyList[symb].volumeRegression[x] = 0
				self.companyList[symb].frequencyRegression[x] = 0


			#update the buffer of values
			self.companyList[symb].volumeRegression[x] += float(t.size)
			self.companyList[symb].frequencyRegression[x] += 1.0


		#
		#	ANOMALY BY TRADER
		#

		if(t.seller not in self.traderList):
			#first value is total value traded, second value is 
			self.traderList[t.seller] = [float(t.size)*float(t.price), 0]
		else:
			self.traderList[t.seller][0] = self.traderList[t.seller][0]*0.9 + 0.1*float(t.size)*float(t.price)

			if (self.traderList[t.seller][1] < self.minTraderTrades):	#only start detecting anomalies per trader after 5
			# trades already recieved
				self.traderList[t.seller][1] += 1
			else:
			# only much larger then expected values
				if((#self.traderList[t.seller] > float(t.size)*float(t.price)*self.senstivityPerTrader or
					self.traderList[t.seller][0] < float(t.size)*float(t.price)/self.senstivityPerTrader)):
					trade_anomaly.append(3)
					print("trader anomaly")


		trade_anomaly = []####################################################




		return trade_anomaly

	def detectError(self, original, compareTo, sensitivity, linearError):
		return (original>=compareTo*sensitivity+linearError*compareTo or original<=compareTo/sensitivity-linearError*compareTo)

class StockData:
	#contains company symbol, polynomial coefficients for best fit line and range within it's considered not anomolalous

	def __init__(self, symbol, stepLength, numberOfRegressors):
		self.symbol = symbol
		self.priceRegression = PriceRegression(numberOfRegressors) #to be changhed for better encapsulation
		self.volumeRegression = []
		self.frequencyRegression = []
		# self.stepLength = stepLength
		self.currTime = []
		self.volumeAvg = 0
		self.frequenceAvg = 0		
		self.currCnt = []
		for x in range(len(stepLength)):
			self.volumeRegression.append(0)
			self.frequencyRegression.append(0)
			self.currTime.append(-5)
			self.currCnt.append(0)

#Should make it more expandable/less messy
class PriceRegression:
	def __init__(self, numOfRegressors):
		self.numOfRegressors = numOfRegressors
		self.xVals = np.empty(numOfRegressors)
		self.yVals = np.empty(numOfRegressors)
		self.currCnt = 0
		self.rangeVal = 1.6 #to be adjusted
		self.coeffList = [0.0, 0.0]
		self.notdetected = True
	
	def addTrade(self, trade):
		#update the buffer of x and y values for linear regression
		self.xVals[self.currCnt] = timeToInt(trade.time)
		self.yVals[self.currCnt] = float(trade.price)

		self.currCnt += 1

		#if the required numbr of trades is reached, line fit coefficents are updated
		if(self.currCnt == self.numOfRegressors):
			self.coeffList = np.polyfit(self.xVals, self.yVals, 1)
			# print (self.companyList[symb].priceCoeffList) #debugging
			self.currCnt = 0
			self.notdetected = True
		

	#compare actual vs predicted value
	def detectError(self, x, y):
		return (y>=(x*self.coeffList[0]+self.coeffList[1])*self.rangeVal  or
				y<=(x*self.coeffList[0]+self.coeffList[1])/self.rangeVal)


def timeToInt(time):
	val = 0
	try:
		val = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f").timestamp()
	except ValueError:

		val = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").timestamp()
	return val
