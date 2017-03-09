import numpy as np
from datetime import datetime

def test(counter):
	global _anomalycounter
	counter+=1
	_anomalycounter+=1
	return

# DETECTION MODULE:	

class Detection:

	stepNumOfStepsPairs = [[30, 4]]	#each pair represents a pair of step length (in seconds)
	# and the number of steps between line fit update
	tickTimeCntPairs = [[0, 0]]	# keeps track of the start time of the current step cycle
	# the number of steps that have already happened

	# how many times more valuable a trade has to be than an average value of a trader to raise an error
	senstivityPerTrader = 9
	senstivityPerSector = 3

	# linear regression of price for this many trades per company
	numberOfRegressors = 10

	def __init__(self):	
		self.companyList = {}
		self.traderList = {}
		self.sectorList = {}
		self.numOfStepVariants = len(self.stepNumOfStepsPairs)


	def reset(self):		
		#setup company data, one-off at the beginning
		self.companyList = {}
		#print("setup")
		#some process to load data from db
		self.numOfStepVariants = len(self.stepNumOfStepsPairs)
		#rolling average for all traders
		#(exponential moving average should make it very computationally efficient)
		self.traderList = {}
		#rolling average for all sectors
		#(exponential moving average should make it very computationally efficient)
		self.sectorList = {}
		

	def setupCompanyData(self, t):
		self.companyList[t.symbol] = StockData(t.symbol, self.stepNumOfStepsPairs, self.numberOfRegressors)
		for x in range(self.numOfStepVariants):
			self.tickTimeCntPairs[x][0] = (int(timeToInt(t.time)/self.stepNumOfStepsPairs[x][0]))*self.stepNumOfStepsPairs[x][0] #rounds down to to the nearest step	

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
				print("price anomaly for x = ", timeToInt(t.time), " y = ", float(t.price)) #debugging
				print("expected x = ", timeToInt(t.time), " y = ", self.companyList[symb].priceRegression.coeffList[0]*timeToInt(t.time) + self.companyList[symb].priceRegression.coeffList[1]) #debugging
				#add price anomaly to category
			# else:
			# 	print("no price anomaly for x = ", timeToInt(t.time), " y = ", float(t.price)) #debugging
			# 	print("expected x = ", timeToInt(t.time), " y = ", self.companyList[symb].priceRegression.coeffList[0]*timeToInt(t.time) + self.companyList[symb].priceRegression.coeffList[1]) #debugging
				trade_anomaly.append(1)


		#
		#	FREQUENCY AND VOLUME REGRESSION
		#

		for x in range(len(self.stepNumOfStepsPairs)): #for every possible tick length/beginning time
			if(timeToInt(t.time) >= self.stepNumOfStepsPairs[x][0]+self.tickTimeCntPairs[x][0]): #if the tick has finished
				if(self.tickTimeCntPairs[x][1] >= self.stepNumOfStepsPairs[x][1]):	#if the number of ticks exceeded maximum (i.e. it's time to upadte the line fit)


					self.tickTimeCntPairs[x][1] = 0



					for company in self.companyList.values():	#every tick, sum the value of voulmes in that step and store, update current step start time and step count

						#
						#	FREQUENCY
						#

						if (company.frequencyRegression[x].detectError(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2), company.frequencyRegression[x].tempYVals)
							and np.all(company.frequencyRegression[x].coeffList != [0.0, 0.0]) and np.all(company.frequencyRegression[x].coeffList != [-1.0, -1.0])):
							print("frequency anomaly for x=", company.frequencyRegression[x].tempYVals, " y=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging[x]
							print("expected x=", self.companyList[symb].frequencyRegression[x].coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.frequencyRegression[x].coeffList[1], " +/- ", self.companyList[symb].frequencyRegression[x].rangeVal) #debugging
							trade_anomaly.append(4)

						if(np.all(company.frequencyRegression[x].coeffList != [0.0, 0.0])): #on second (first guaranteed completed) and subsequent passes
							company.frequencyRegression[x].updateCoeffs()
						else:
							company.frequencyRegression[x].coeffList = [-1.0, -1.0]	#mark the beginning of a first complete pass


						company.frequencyRegression[x].yVals[self.tickTimeCntPairs[x][1]] = company.frequencyRegression[x].tempYVals
						company.frequencyRegression[x].xVals[self.tickTimeCntPairs[x][1]] = self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)
						company.frequencyRegression[x].tempYVals = 0


						#
						#	VOLUME
						#

						if (company.volumeRegression[x].detectError(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2), sum(company.volumeRegression[x].tempYVals))
							and np.all(company.volumeRegression[x].coeffList != [0.0, 0.0]) and np.all(company.volumeRegression[x].coeffList != [-1.0, -1.0])):

							trade_anomaly.append(2)

							print(str(t.time)+" volume anomaly")
							print("volume anomaly for y=", sum(company.volumeRegression[x].tempYVals), " x=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							print("expected y=", company.volumeRegression[x].coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.volumeRegression[x].coeffList[1], " +/- ", company.volumeRegression[x].rangeVal) #debugging#
							print("coeff is ", company.volumeRegression[x].coeffList)
						# else:
							# print(str(t.time)+" NO volume anomaly")
							# print("NO anomaly for y=", sum(company.volumeRegression.tempYVals), " x=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							# print("expected y=", company.volumeRegression.coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.volumeRegression.coeffList[1], " +/- ", company.volumeRegression.rangeVal) #debugging
							# print("coeff is ", company.volumeRegression.coeffList)
						

						
						if(np.all(company.volumeRegression[x].coeffList != [0.0, 0.0])): #on second (first guaranteed completed) and subsequent passes
							company.volumeRegression[x].updateCoeffs()
						else:
							company.volumeRegression[x].coeffList = [-1.0, -1.0]	#mark the beginning of a first complete pass


						# print(self.tickTimeCntPairs[x][1])
						company.volumeRegression[x].yVals[self.tickTimeCntPairs[x][1]] = sum(company.volumeRegression[x].tempYVals)
						company.volumeRegression[x].xVals[self.tickTimeCntPairs[x][1]] = self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)
						company.volumeRegression[x].tempYVals = []

					self.tickTimeCntPairs[x][1] += 1
					self.tickTimeCntPairs[x][0] += self.stepNumOfStepsPairs[x][0]


				else:				
					for company in self.companyList.values():	#every tick, sum the value of voulmes in that step and store, update current step start time and step count


						#
						#	FREQUENCY
						#

						# print(self.tickTimeCntPairs[x][1], self.stepNumOfStepsPairs[x][1])
						if (company.frequencyRegression[x].detectError(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2), company.frequencyRegression[x].tempYVals)
							and np.all(company.frequencyRegression[x].coeffList != [0.0, 0.0]) and np.all(company.volumeRegression[x].coeffList != [-1.0, -1.0])):
							# print("frequency anomaly for x=", company.frequencyRegression[x].tempYVals, " y=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							# print("expected x=", self.companyList[symb].frequencyRegression[x].coeffList[0]*self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)+company.frequencyRegression[x].coeffList[1], " +/- ", self.companyList[symb].frequencyRegression[x].rangeVal) #debugging
							trade_anomaly.append(4)
						# else:
						# 	print("ratio:", self.companyList[symb].frequencyRegression[x].coeffList[0]*self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)+company.frequencyRegression[x].coeffList[1], " +/- ", self.companyList[symb].frequencyRegression[x].rangeVal)

						company.frequencyRegression[x].yVals[self.tickTimeCntPairs[x][1]] = company.frequencyRegression[x].tempYVals #TODO what happens where no trade comes in during the whole tick
						company.frequencyRegression[x].xVals[self.tickTimeCntPairs[x][1]] = self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)
						company.frequencyRegression[x].tempYVals = 0
						# print(self.tickTimeCntPairs[x][1])
						# print(self.tickTimeCntPairs[x][0])

						#
						#	VOLUME
						#

						# print(self.tickTimeCntPairs[x][1], self.stepNumOfStepsPairs[x][1])
						if (company.volumeRegression[x].detectError(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2), sum(company.volumeRegression[x].tempYVals))
							and np.all(company.volumeRegression[x].coeffList != [0.0, 0.0]) and np.all(company.volumeRegression[x].coeffList != [-1.0, -1.0])):

							print("volume anomaly for y=", sum(company.volumeRegression[x].tempYVals), " x=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							print("expected y=", company.volumeRegression[x].coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.volumeRegression[x].coeffList[1], " +/- ", company.volumeRegression[x].rangeVal) #debugging
							print("coeff is ", company.volumeRegression[x].coeffList)
							trade_anomaly.append(2)
						# else:
							# print(str(t.time)+" NO anomaly")
							# print("NO anomaly for y=", sum(company.volumeRegression.tempYVals), " x=", self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)) #debugging
							# print("expected y=", company.volumeRegression.coeffList[0]*(self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2))+company.volumeRegression.coeffList[1], " +/- ", company.volumeRegression.rangeVal) #debugging
							# print("coeff is ", company.volumeRegression.coeffList)
						


						company.volumeRegression[x].yVals[self.tickTimeCntPairs[x][1]] = sum(company.volumeRegression[x].tempYVals)
						company.volumeRegression[x].xVals[self.tickTimeCntPairs[x][1]] = self.tickTimeCntPairs[x][0]+(self.stepNumOfStepsPairs[x][0]/2)
						company.volumeRegression[x].tempYVals = []
						# print(self.tickTimeCntPairs[x][1])
						# print(self.tickTimeCntPairs[x][0])



					self.tickTimeCntPairs[x][1] += 1
					#print(self.tickTimeCntPairs[x][1])
					self.tickTimeCntPairs[x][0] += self.stepNumOfStepsPairs[x][0]



		self.companyList[symb].volumeRegression[x].tempYVals.append(float(t.size))

		self.companyList[symb].frequencyRegression[x].tempYVals += 1


		#
		#	ANOMALY BY TRADER
		#

		if(t.seller not in self.traderList):
			#first value is total value traded, second value is 
			self.traderList[t.seller] = [float(t.size)*float(t.price), 0]
		else:
			self.traderList[t.seller][0] = self.traderList[t.seller][0]*0.9 + 0.1*float(t.size)*float(t.price)

			if (self.traderList[t.seller][1] < 5):	#only start detecting anomalies per trader after 5
			# trades already recieved
				self.traderList[t.seller][1] += 1
			else:
			# only much larger then expected values
				if((#self.traderList[t.seller] > float(t.size)*float(t.price)*self.senstivityPerTrader or
					self.traderList[t.seller][0] < float(t.size)*float(t.price)/self.senstivityPerTrader)):
					trade_anomaly.append(3)
					print("trader anomaly")

		#
		#	SECTOR VALUE ANOMALY
		#

		# if(t.sector not in self.sectorList):
		# 	self.sectorList[t.sector] = [float(t.size)*float(t.price), 0]
		# else:
		# 	self.sectorList[t.sector][0] = self.sectorList[t.sector][0]*0.9 + 0.1*float(t.size)*float(t.price)

		# 	if (self.sectorList[t.sector][1] > 2):	#only start detecting anomalies per sector after 2 cycles
		# 		self.sectorList[t.sector][0] += float(t.size)*float(t.price)

		# for x in range(len(self.stepNumOfStepsPairs)): #after the finish of every tick series
		# 	if()
		
		# 		if((self.sectorList[t.sector] > float(t.size)*float(t.price)*self.senstivityPerSector or
		# 			self.sectorList[t.sector][0] < float(t.size)*float(t.price)/self.senstivityPerTrader)):
		# 			trade_anomaly.append(5)
		# 			print("sector anomaly")	
		
		return trade_anomaly

class StockData:
	#contains company symbol, polynomial coefficients for best fit line and range within it's considered not anomolalous

	def __init__(self, symbol, stepNumOfStepsPairs, numberOfRegressors):
		self.symbol = symbol
		self.priceRegression = PriceRegression(numberOfRegressors) #to be changhed for better encapsulation
		self.volumeRegression = {}
		self.frequencyRegression = {}
		for x in range(len(stepNumOfStepsPairs)):
			self.volumeRegression[x] = VolumeRegression(0, stepNumOfStepsPairs[x][1])
			self.frequencyRegression[x] = AvgOverTimeRegression(0, stepNumOfStepsPairs[x][1])

#Should make it more expandable/less messy
class PriceRegression:
	def __init__(self, numOfRegressors):
		self.numOfRegressors = numOfRegressors
		self.xVals = np.empty(numOfRegressors)
		self.yVals = np.empty(numOfRegressors)
		self.currCnt = 0
		self.rangeVal = 3 #to be adjusted
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
		return (y>=(x*self.coeffList[0]+self.coeffList[1])*self.rangeVal or
				y<=(x*self.coeffList[0]+self.coeffList[1])/self.rangeVal)
	
	# def updateCoeffs(self):
	# 	self.coeffList = np.polyfit(self.xVals, self.yVals, 1)

#Should make it more expandable/less messy
class AvgOverTimeRegression:
	def __init__(self, stepNumOfStepsPairsIndex, numOfSteps):
		# self.stepNumOfStepsPairsIndex = stepNumOfStepsPairsIndex #for better encapsulation in the future
		self.xVals = np.zeros(numOfSteps)
		self.yVals = np.zeros(numOfSteps)
		self.tempYVals = 0
		self.rangeVal = 3 #changed for testing
		self.coeffList = [0.0, 0.0]

	# compare actual vs predicted value
	def detectError(self, x, y):
		return (y>=(x*self.coeffList[0]+self.coeffList[1])*self.rangeVal + self.rangeVal*self.linearError() or
				y<=(x*self.coeffList[0]+self.coeffList[1])/self.rangeVal - self.linearError())
	
	def updateCoeffs(self):
		self.coeffList = np.polyfit(self.xVals, self.yVals, 1)

	def linearError(self):
		return np.average(self.yVals)

class VolumeRegression(AvgOverTimeRegression):
	def __init__(self, stepNumOfStepsPairsIndex, numOfSteps):
		super().__init__(stepNumOfStepsPairsIndex, numOfSteps)
		self.tempYVals = []
		self.rangeVal = 5 #changed for testing


def timeToInt(time):
	val = 0
	try:
		val = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f").timestamp()
	except ValueError:
		val = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").timestamp()
	return val