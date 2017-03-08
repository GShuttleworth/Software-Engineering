import mysql.connector
from app import mtrade
from os.path import isfile, getsize
import os


class Database:

	def __init__(self, state=1):
		# Assumes schema is already implemented
		self.conn = mysql.connector.connect(user='root', password='andypandy', host='127.0.0.1', database='cs261')
		self.c = self.conn.cursor(buffered=True)
		self.state = state  # Default is 1 (live)

	# General purpose functions
	def query(self, query, params):
		# for basic queries
		return self.c.execute(query, params)

	def action(self, query, params):
		#print("Making insertion")
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

	def getAverage(self, sym):  # Returns list, avgPrice at 1 and avgVol at 2
		table = "averages_live"
		if(self.state != 1):
			table = "averages_static"
		query = "SELECT * FROM " + table + " WHERE symbol='%s'"
		params = [sym]
		data = self.query(query, params)
		# should only return 1 row right, if it exists
		try:
			avg_exists = data.fetchone()
		except AttributeError:
			return -1
		return avg_exists


	def updateAverage(self, sym, price, vol, num):
		table = "averages_live"
		if(self.state != 1):
			table = "averages_static"
		query = "UPDATE " + table + \
				" SET averagePrice='%s', averageVolume='%s', numTrades='%s' WHERE symbol='%s'"
		params = [price, vol, num, sym]
		updated = self.action(query, params)
		#print("Total number of rows updated :", updated)
		if(updated == 0):  # check to see if it was updated
			# add row
			query = "INSERT INTO " + table + " VALUES ('%s','%s','%s','%s')"
			params = [sym, price, vol, 0]
			updated = self.action(query, params)

	def addTransaction(self,data, state):
		if(isinstance(data, mtrade.TradeData)):
			print("Adding a transaction")
			query = ""
			if(state == 1):
				query = """INSERT INTO trans_live VALUES (NULL, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"""
			else:
				query = "INSERT INTO trans_static VALUES (NULL, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
			tradeid=-1
			params = (data.time, data.buyer, data.seller, data.price, data.size,
			data.currency, data.symbol, data.sector, data.bidPrice, data.askPrice)
			self.action(query, params)

			tradeid=self.c.lastrowid
			# Update the averages tables
			avgData = self.getAverage(data.symbol)
			if(avgData == -1):
				# No averages present
				self.updateAverage(data.symbol, data.price, data.size, 0)
				return tradeid

			avgPrice, avgVolume, numTrades = avgData[1], avgData[2], avgData[3]
			# Recalculate the averages
			avgPrice *= numTrades
			avgVolume *= numTrades
			avgPrice += float(data.price)
			avgVolume += int(data.size)
			numTrades += 1
			avgPrice /= numTrades
			avgVolume /= numTrades
			self.updateAverage(data.symbol, avgPrice, avgVolume, numTrades)
			return tradeid
		else:
			return -1

	def anomalycount(self):
		table = "anomalies_live"
		return self.getcount(table)

	def tradecount(self):
		table = "trans_live"
		return self.getcount(table)

	def getcount(self, table):
		query = "SELECT COUNT(*) FROM " + table
		params =[]
		data = self.query(query, params)
		try:
			t = data.fetchone()
		except AttributeError:
			return 0
		return t[0]

	def tradevalue(self):
		query = "SELECT SUM(price * volume) FROM trans_live"
		params = []
		data = self.query(query, params)
		try:
			t = data.fetchone()
		except AttributeError:
			return 0
		return t[0]

	def getAveragePrice(self, sym):
		return self.getAverage(sym)[1]

	#def getAverageVolume(self, sym):
	#	return self.getAverage(sym)[2]
	#		query = "INSERT INTO " + table + " VALUES ('%s','%s','%s','%s')"
	#		params = [sym, price, vol, 0]
	#		updated = self.action(query, params)

	def getTransactions(self, q):
		data = self.query(q)
		transactions = []
		for row in data:
			transactions.append(mtrade.TradeData(row[0], row[1], row[2], row[3], row[
				4], row[5], row[6], row[7], row[8], row[9]))

		return transactions

	def clear(self, date):
		# delete all entries with the same date
		table = "trans_live"
		if(self.state == 1):
			table = "trans_static"

		query = "DELETE FROM " + table + " WHERE time='%s'"
		params = [date]
		self.action(query, params)
		return 1
	
	def clearall(self,state):
		#delete all entries from trades and anomalies
		try:
			table = "trans_live"
			if(state==0):
				table = "static_live"
			query = "DELETE FROM " + table
			params = []
			self.action(query, params)
			table = "trans_static"
			if(state==0):
				table = "anomalies_static"
			query = "DELETE FROM " + table
			params = []
			self.action(query, params)
		except:
			return False
		return True
		
	# gets all the anomalies for the table, returns a list of anomaly objects
	def getAnomalies(self, done):
		table = "anomalies_live"
		if(self.state != 1):
			table = "anomalies_static"  # shouldn't exist but for the sake of it
		query = "SELECT id,tradeid,category FROM " + table + " WHERE actiontaken='%s'"
		params = [done]
		data = self.query(query, params)
		try:
			rows = data.fetchall()
		except AttributeError:
			rows = []
		anomalies = []
		for row in rows:
			# gonna get complicated
			# each row needs to do another sql query to get trade and turn into
			# TradeData
			table = "trans_live"
			if(self.state != 1):
				table = "trans_static"
			query = "SELECT time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + \
				table + " WHERE id='%s'"
			params = [row[1]]
			data = self.query(query, params)
			t = data.fetchone()
			trade_1 = mtrade.to_TradeData(t)
			a = mtrade.Anomaly(row[0], trade_1, row[2])
			anomalies.append(a)
		return anomalies
	
	def getAnomalyById(self, id):
		# Useful function for the drill down stuff
		table1 = "anomalies_live"
		table2 = "trans_live"
		if(self.state != 1):
			table1 = "anomalies_static"
			tabel2 = "trans_static"
		query = "SELECT * FROM " + table1 + " WHERE id='%s'"
		print(id)
		params = [id]
		result = self.query(query, params)
		#print("Row count: " + str(result.rowcount()))
		row = result.fetchone()  # Only one result per id
		query = "SELECT time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + \
			table2 + " WHERE id='%s'"
		params = [row[1]]
		data = self.query(query, params)
		t = data.fetchone()
		trade = mtrade.to_TradeData(t)
		return mtrade.Anomaly(row[0], trade, row[2])

	def addAnomaly(self, tradeid, category, state):
		anomalyid = -1
		table = "anomalies_live"
		if(state != 1):
			table = "anomalies_static"

		query = "INSERT INTO " + table + " VALUES(NULL, '%s', '%s', 0)"
		params = [tradeid, category]
		self.action(query, params)
		anomalyid = self.c.lastrowid
		return anomalyid

	def getAveragePrice(self, sym):
		return self.getAverage(sym)[1]

	def getAverageVolume(self, sym):
		return self.getAverage(sym)[2]

	def getTradesForDrillDown(self, sym, id):
		# Return set of recent trades before and after anomaly
		# Get trade id
		table = "anomalies_live"
		if(self.state != 1):
			table = "anomalies_static"
		query = "SELECT tradeid FROM " + table + " WHERE id='%s'"
		params = [id]
		tradeId = self.query(query, params).fetchone()[0]
		table = "trans_live"
		if(self.state != 1):
			table = "trans_static"
		# Get trades beforehand
		query = "SELECT time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + \
			table + " WHERE(symbol='%s' and id<='%s') ORDER BY datetime(time) DESC LIMIT 8"
		params = [sym, tradeId]
		rows = self.query(query, params)
		trades = []
		for row in rows: 
			trade = mtrade.to_TradeData(row)
			trades.append(trade)
			#print(trades)

		#print(trades)
		trades = trades[::-1] # Reverses the order of the trades, as they are currently in descending, not ascending order
		#print(trades)
		query = "SELECT time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + \
			table + " WHERE(symbol='%s' and id>'%s') ORDER BY datetime(time) ASC LIMIT 7"
		params = [sym, tradeId]
		results = self.query(query, params)
		for res in results: 
			trade = mtrade.to_TradeData(res)
			trades.append(trade)
			#print(trades)

		return trades
