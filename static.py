#!/usr/bin/env python
#queue_fifo.py

import csv
import Queue

class TradeData:
	def __init__(self, time, buy, sell, p, s, currency, symbol, sector, bidP, askP):
		self.time = time
		self.buyer = buy
		self.seller = sell
		self.price = p
		self.size = s
		self.currency = currency
		self.symbol = symbol
		self.sector = sector
		self.bidPrice = bidP
		self.askPrice = askP	

classqueue = Queue.Queue()

with open('trades.csv', 'r') as csvfile:
    
    reader = csv.reader(csvfile, delimiter = ',')

    for row in reader:
    	if row[0] == 'time':
    		continue
    	else:
    		classqueue.put(TradeData(row[0], row[1], row[2], float(row[3]), 
    			int(row[4]), row[5], row[6], row[7], float(row[8]), float(row[9])))

def getFromQ(q):

	while not classqueue.empty():
	    data = classqueue.get()
	    return data