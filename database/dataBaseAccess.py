import sqlite3, TradeData

class Database:
	def __init__(self, state=1):
		self.conn = sqlite3.connect("dataBase.db")
		self.c = self.conn.cursor()
		self.state = state # Default is 1 (live)

	# General purpose functions
	def query(self, query):
		# for basic queries
		return c.execute(query)

	def action(self, query):
		# for update, insert, etc
		self.c.execute(query)
		self.conn.commit()

	def changeState(self, state):
		# Change between live and static
		if(state == 1 or state == 0):
			self.state = state

	def close(self):
		# Close the connection to the database
		conn.close()

	def addTransaction(self, data):
		if(isinstance(data, TradeData.TradeData)):
			if(self.state == "1"):
				query = "insert into trans_live values (NULL, " + data.time + "," + data.buyer + "," + data.seller + "," + data.price + "," + data.size + "," + data.currency + "," + data.symbol + "," + data.sector + "," + bidPrice + "," + askPrice + ");"
				self.query(query)
			else:
				query = "insert into trans_static values (NULL, " + data.time + "," + data.buyer + "," + data.seller + "," + data.price + "," + data.size + "," + data.currency + "," + data.symbol + "," + data.sector + "," + bidPrice + "," + askPrice + ");"
				self.query(query)

	def getTransactions(self, q):
		data = self.query(q)
		transactions = []
		for row in data:
			transactions.append(TradeData.TradeData(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]))

		return transactions

	
	

				
		
		
		
