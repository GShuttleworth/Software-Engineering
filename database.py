import sqlite3
from trade import *

class Database:
	def __init__(self, state=1):
		self.conn = sqlite3.connect("database.db")
		self.c = self.conn.cursor()
		self.state = state # Default is 1 (live)

	# General purpose functions
	def query(self, query, params):
		# for basic queries
		return self.c.execute(query,params)

	def action(self, query, params):
		# for update, insert, etc
		self.c.execute(query, params)
		self.conn.commit()
		return self.c.rowcount
	
	def changeState(self, state):
		# Change between live and static
		if(state == 1 or state == 0):
			self.state = state

	def close(self):
		# Close the connection to the database
		self.conn.close()

	def addTransaction(self, data):
		if(isinstance(data, TradeData)):
			query = ""
			if(self.state == 1):
				query = "INSERT INTO trans_live VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
			else:
				query = "INSERT INTO trans_static VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
			params = (data.time, data.buyer, data.seller, data.price, data.size, data.currency, data.symbol, data.sector, data.bidPrice, data.askPrice)
			self.action(query,params)

	def getTransactions(self, q):
		data = self.query(q)
		transactions = []
		for row in data:
			transactions.append(TradeData(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))

		return transactions

	def getAverage(self, sym):
		avg = -1 #sanity check!
		table = "avg_live"
		if(self.state != 1):
			table = "avg_static"
		
		query = "SELECT averagePrice FROM " + table + " WHERE symbol=?"
		params = [sym]
		data = self.query(query,params)
		#should only return 1 row right, if it exists
		avg_exists = data.fetchone()
		if(avg_exists):
			avg=avg_exists
		return avg

	def updateAverage(self, sym, val):
		#attempts to update
		table = "avg_live"
		if(self.state != 1):
			table = "avg_static"
		query = "UPDATE " + table + " SET averagePrice=? WHERE symbol=?"
		params = [val,sym]
		updated = self.action(query,params)
		#print("Total number of rows updated :", updated)
		if(updated==0): #check to see if it was updated
			#add row
			query = "INSERT INTO " + table + " VALUES (NULL,?,?)"
			params = [sym,val]
			updated = self.action(query,params)
			#print("Number of INSERTED rows: ", updated)
		
