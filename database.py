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

	
	

				
		
		
		
