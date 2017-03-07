import numpy as np
from datetime import datetime

def test(counter):
	global _anomalycounter
	counter+=1
	_anomalycounter+=1
	return

# DETECTION MODULE:	

class Detection:

	stepNumOfStepsPairs = [[30, 10]]	#each pair represents a pair of step length (in seconds)
	# and the number of steps between line fit update
	tickTimeCntPairs = [[0, 0]]	# keeps track of the start time of the current step cycle
	# the number of steps that have already happened

	# how many times more valuable a trade has to be than an average value of a trader to raise an error
	senstivityPerTrader = 5

	# linear regression of price for this many trades per company
	_numberOfRegressors = 10

	def __init__(self):		
		#setup company data, one-off at the beginning
		self.companyList = {}
		#some process to load data from db
		self.numOfStepVariants = len(self.stepNumOfStepsPairs)

		#rolling average for all traders
		#(exponential moving average should make it very computationally efficient)
		self.traderList = {}
		

	def setupCompanyData(self, t):
		self.companyList[t.symbol] = StockData(t.symbol, self.stepNumOfStepsPairs)
		for x in range(self.numOfStepVariants):
			self.tickTimeCntPairs[x][0] = (int(timeToInt(t.time)/self.stepNumOfStepsPairs[x][0]))*self.stepNumOfStepsPairs[x][0] #rounds down to to the nearest step	
	
	def new_anomaly(self,db,tradeid,t,category):
		global _sessionslock
		global _anomalycounter
		global _sessions
		anomalyid = -1
		anomalyid = db.addAnomaly(tradeid, category)
		newAnomaly = mtrade.Anomaly(anomalyid, t, category) #todo change 3
		#doSomething with the anomaly
		_anomalycounter+=1
			#for each key in session, add this anomaly
		_sessionslock.acquire
		for key in _sessions:
			_sessions[key].put(newAnomaly)
		_sessionslock.release
	

	def detect(self, t):

		#######
		#anomalies
		trade_anomaly = []

		symb = t.symbol

		# create a StockData object for every company
		if (symb not in self.companyList):
			self.setupCompanyData(t)
				
		#	PRICE REGRESSION

		self.companyList[symb].priceRegression.addTrade(t)
		if(np.all(self.companyList[symb].priceRegression.coeffList != [0.0, 0.0])):
			# print(self.companyList[symb].priceCoeffList) #debugging
			if(self.companyList[symb].priceRegression.detectError(timeToInt(t.time), float(t.price))):
				print("price anomaly") #debugging
				#add price anomaly to category
				trade_anomaly.append(1)


		for x in range(len(self.stepNumOfStepsPairs)): #for every possible tick length/beginning time
			if(timeToInt(t.time) >= self.stepNumOfStepsPairs[x][0]+self.tickTimeCntPairs[x][0]): #if the tick has finished
				if(self.tickTimeCntPairs[x][1] >= self.stepNumOfStepsPairs[x][1]):	#if the number of ticks exceeded maximum (i.e. it's time to upadte the line fit)
					
					self.tickTimeCntPairs[x][1] = 0
					#print(self.tickTimeCntPairs[x][1])

					for company in self.companyList.values():	#every tick, sum the value of voulmes in that step and store, update current step start time and step count
						if (company.volumeRegression.detectError(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2), sum(company.volumeRegression.tempYVals))
							and np.all(company.volumeRegression.coeffList != [0.0, 0.0]) and np.all(company.volumeRegression.coeffList != [-1.0, -1.0])):

							trade_anomaly.append(2)

							# print(str(t.time)+" volume anomaly")
							# print("volume anomaly for y=", sum(company.volumeRegression.tempYVals), " x=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							# print("expected y=", company.volumeRegression.coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.volumeRegression.coeffList[1], " +/- ", company.volumeRegression.rangeVal) #debugging#
							# print("coeff is ", company.volumeRegression.coeffList)
						# else:
							# print(str(t.time)+" NO volume anomaly")
							# print("NO anomaly for y=", sum(company.volumeRegression.tempYVals), " x=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							# print("expected y=", company.volumeRegression.coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.volumeRegression.coeffList[1], " +/- ", company.volumeRegression.rangeVal) #debugging
							# print("coeff is ", company.volumeRegression.coeffList)
						

						
						if(np.all(company.volumeRegression.coeffList != [0.0, 0.0])): #on second (first guaranteed completed) and subsequent passes
							company.volumeRegression.updateCoeffs()
						else:
							company.volumeRegression.coeffList = [-1.0, -1.0]	#mark the beginning of a first complete pass


						# print(self.tickTimeCntPairs[x][1])
						company.volumeRegression.yVals[self.tickTimeCntPairs[x][1]] = sum(company.volumeRegression.tempYVals)
						company.volumeRegression.xVals[self.tickTimeCntPairs[x][1]] = self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)
						company.volumeRegression.tempYVals = []

					self.tickTimeCntPairs[x][1] += 1
					self.tickTimeCntPairs[x][0] += self.stepNumOfStepsPairs[x][0]

				else:
					#print(self.tickTimeCntPairs[x][1])

					for company in self.companyList.values():	#every tick, sum the value of voulmes in that step and store, update current step start time and step count
						# print(self.tickTimeCntPairs[x][1], self.stepNumOfStepsPairs[x][1])
						if (company.volumeRegression.detectError(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2), sum(company.volumeRegression.tempYVals))
							and np.all(company.volumeRegression.coeffList > [0.0, 0.0]) and np.all(company.volumeRegression.coeffList != [-1.0, -1.0])):

							# print("volume anomaly for y=", sum(company.volumeRegression.tempYVals), " x=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							# print("expected y=", company.volumeRegression.coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.volumeRegression.coeffList[1], " +/- ", company.volumeRegression.rangeVal) #debugging
							# print("coeff is ", company.volumeRegression.coeffList)
							trade_anomaly.append(2)
						# else:
							# print(str(t.time)+" NO anomaly")
							# print("NO anomaly for y=", sum(company.volumeRegression.tempYVals), " x=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							# print("expected y=", company.volumeRegression.coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.volumeRegression.coeffList[1], " +/- ", company.volumeRegression.rangeVal) #debugging
							# print("coeff is ", company.volumeRegression.coeffList)
						


						company.volumeRegression.yVals[self.tickTimeCntPairs[x][1]] = sum(company.volumeRegression.tempYVals)
						company.volumeRegression.xVals[self.tickTimeCntPairs[x][1]] = self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)
						company.volumeRegression.tempYVals = []
						# print(self.tickTimeCntPairs[x][1])
						# print(self.tickTimeCntPairs[x][0])

					self.tickTimeCntPairs[x][1] += 1
					#print(self.tickTimeCntPairs[x][1])
					self.tickTimeCntPairs[x][0] += self.stepNumOfStepsPairs[x][0]



		self.companyList[symb].volumeRegression.tempYVals.append(float(t.size))

		#
		#	FREQUENCY REGRESSION
		#

		for x in range(len(self.stepNumOfStepsPairs)): #for every possible tick length/beginning time
			if(timeToInt(t.time) >= self.stepNumOfStepsPairs[x][0]+self.tickTimeCntPairs[x][0]): #if the tick has finished
				if(self.tickTimeCntPairs[x][1] >= self.stepNumOfStepsPairs[x][1]):	#if the number of ticks exceeded maximum (i.e. it's time to upadte the line fit)


					self.tickTimeCntPairs[x][1] = 0

					for company in self.companyList.values():	#every tick, sum the value of voulmes in that step and store, update current step start time and step count
						if (company.frequencyRegression.detectError(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2), company.frequencyRegression.tempYVals)
							and np.all(company.frequencyRegression.coeffList > [0.0, 0.0]) and np.all(company.volumeRegression.coeffList != [-1.0, -1.0])):
							# print("frequency anomaly for x=", company.frequencyRegression.tempYVals, " y=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							# print("expected x=", self.companyList[symb].frequencyRegression.coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.frequencyRegression.coeffList[1], " +/- ", self.companyList[symb].frequencyRegression.rangeVal) #debugging
							trade_anomaly.append(4)

						if(np.all(company.frequencyRegression.coeffList != [0.0, 0.0])): #on second (first guaranteed completed) and subsequent passes
							company.frequencyRegression.updateCoeffs()
						else:
							company.frequencyRegression.coeffList = [-1.0, -1.0]	#mark the beginning of a first complete pass


						company.frequencyRegression.yVals[self.tickTimeCntPairs[x][1]] = company.frequencyRegression.tempYVals
						company.frequencyRegression.xVals[self.tickTimeCntPairs[x][1]] = self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)
						company.frequencyRegression.tempYVals = 0

					self.tickTimeCntPairs[x][1] += 1
					self.tickTimeCntPairs[x][0] += self.stepNumOfStepsPairs[x][0]

				else:				
					for company in self.companyList.values():	#every tick, sum the value of voulmes in that step and store, update current step start time and step count
						# print(self.tickTimeCntPairs[x][1], self.stepNumOfStepsPairs[x][1])
						if (company.frequencyRegression.detectError(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2), company.frequencyRegression.tempYVals)
							and np.all(company.frequencyRegression.coeffList > [0.0, 0.0]) and np.all(company.volumeRegression.coeffList != [-1.0, -1.0])):
							# print("frequency anomaly for x=", company.frequencyRegression.tempYVals, " y=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							# print("expected x=", self.companyList[symb].frequencyRegression.coeffList[0]*self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)+company.frequencyRegression.coeffList[1], " +/- ", self.companyList[symb].frequencyRegression.rangeVal) #debugging
							trade_anomaly.append(4)

						company.frequencyRegression.yVals[self.tickTimeCntPairs[x][1]] = company.frequencyRegression.tempYVals #TODO what happens where no trade comes in during the whole tick
						company.frequencyRegression.xVals[self.tickTimeCntPairs[x][1]] = self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)
						company.frequencyRegression.tempYVals = 0
						# print(self.tickTimeCntPairs[x][1])
						# print(self.tickTimeCntPairs[x][0])

					self.tickTimeCntPairs[x][1] += 1
					#print(self.tickTimeCntPairs[x][1])
					self.tickTimeCntPairs[x][0] += self.stepNumOfStepsPairs[x][0]



		self.companyList[symb].frequencyRegression.tempYVals += 1 #might delete that variable in the future

		#
		#	ANOMALY BY TRADER
		#

		if(t.seller not in self.traderList):
			#first value is total value traded, second value is 
			self.traderList[t.seller] = [float(t.size)*float(t.price), 0]
		else:
			self.traderList[t.seller][0] = self.traderList[t.seller][0]*0.9 + 0.1*float(t.size)*float(t.price)

			if (self.traderList[t.seller][1] < 10):	#only start detecting anomalies per trader after 10
			# trades already recieved
				self.traderList[t.seller][1] += 1
			else:
			# only much larger then expected values
				if((#self.traderList[t.seller] > float(t.size)*float(t.price)*self.senstivityPerTrader or
					self.traderList[t.seller][0] < float(t.size)*float(t.price)/self.senstivityPerTrader)):
					trade_anomaly.append(3)
		
		return trade_anomaly



class StockData:
	#contains company symbol, polynomial coefficients for best fit line and range within it's considered not anomolalous
	def __init__(self, symbol, stepNumOfStepsPairs):
		self.symbol = symbol
		self.priceRegression = PriceRegression(10) #to be changhed for better encapsulation
		self.volumeRegression = VolumeRegression(0, stepNumOfStepsPairs[0][1])
		self.frequencyRegression = AvgOverTimeRegression(0, stepNumOfStepsPairs[0][1])

#Should make it more expandable/less messy
class PriceRegression:
	def __init__(self, numOfRegressors):
		self.numOfRegressors = numOfRegressors
		self.xVals = np.empty(numOfRegressors)
		self.yVals = np.empty(numOfRegressors)
		self.currCnt = 0
		self.rangeVal = 0.4 #to be adjusted
		self.coeffList = [0.0, 0.0]
	
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
		

	#compare actual vs predicted value
	def detectError(self, x, y):
		return (y>=(x*self.coeffList[0]+self.coeffList[1])*(1+self.rangeVal) or
				y<=(x*self.coeffList[0]+self.coeffList[1])*(1-self.rangeVal))
	
	# def updateCoeffs(self):
	# 	self.coeffList = np.polyfit(self.xVals, self.yVals, 1)

#Should make it more expandable/less messy
class AvgOverTimeRegression:
	def __init__(self, stepNumOfStepsPairsIndex, numOfSteps):
		# self.stepNumOfStepsPairsIndex = stepNumOfStepsPairsIndex #for better encapsulation in the future
		self.xVals = np.zeros(numOfSteps)
		self.yVals = np.zeros(numOfSteps)
		self.tempYVals = 0
		self.rangeVal = 0.4 #changed for testing
		self.coeffList = [0.0, 0.0]

	# compare actual vs predicted value
	def detectError(self, x, y):
		return (y>=(x*self.coeffList[0]+self.coeffList[1])*(1+self.rangeVal) or
				y<=(x*self.coeffList[0]+self.coeffList[1])*(1-self.rangeVal))
	
	def updateCoeffs(self):
		self.coeffList = np.polyfit(self.xVals, self.yVals, 1)

class VolumeRegression(AvgOverTimeRegression):
	def __init__(self, stepNumOfStepsPairsIndex, numOfSteps):
		super().__init__(stepNumOfStepsPairsIndex, numOfSteps)
		self.tempYVals = []
		self.rangeVal = 0.5 #changed for testing


def timeToInt(time):
	val = 0
	try:
		val = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f").timestamp()
	except ValueError:
		val = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").timestamp()
	return val
