#!/usr/bin/env python

import csv
import Queue
import TradeData

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