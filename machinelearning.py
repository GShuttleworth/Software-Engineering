import numpy as np

class Point:
	def __init__ (self, x, y):
		self.x = x
		self.y = y

class Averaging:
	@staticmethod
	def average(list, num):
		outputLength = int((len(list)-1)/num + 1)
		outputList = np.empty(outputLength)
		avg = 0
		for x in range(outputLength):
			for y in range(num):
				avg += list[x*num+y]

			outputList[x] = avg/num
			avg = 0

		avg = 0
		cnt = 0

		for x in range(len(list)-(outputLength-1)*num):
			avg += list[(outputLength-1)*num+x]
			cnt += 1

		outputList[outputLength-1] = avg/cnt

		return outputList

class TrendLines:
	@staticmethod
	def trendLine(listX, listY, degree):
		return np.polyfit(listX, listY, degree)
	def isOk(polyCoeffs, xCoord, yCoord, range):
		return (yCoord<=(xCoord*polyCoeffs[0]+polyCoeffs[1])*(1+range) and 
				yCoord>=(xCoord*polyCoeffs[0]+polyCoeffs[1])*(1-range))


xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0 ,6.0 ,7.0, 8.0, 9.0])
ys = np.array([100.0, 110.0, 125.0, 144.0, 167.0, 199.0, 251.0, 321.0, 460.0, 600.0])
lX = Averaging.average(xs, 2)
lY = Averaging.average(ys, 2)

degree = 1

trends = TrendLines.trendLine(lX, lY, degree)

print ("%d*x + %d" % (trends[0], trends[1]))

print (TrendLines.isOk(trends, 5, 250, 0.07))
