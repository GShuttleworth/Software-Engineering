import sqlite3
from trade import *


class Database:

	def __init__(self, state=1):
		self.conn = sqlite3.connect("database.db")
		self.c = self.conn.cursor()
		self.state = state  # Default is 1 (live)

	# General purpose functions
	def query(self, query, params):
		# for basic queries
		return self.c.execute(query, params)

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

	def getAverage(self, sym):  # Returns list, avgPrice at 1 and avgVol at 2
		table = "averages_live"
		if(self.state != 1):
			table = "averages_static"
		query = "SELECT * FROM " + table + " WHERE symbol=?"
		params = [sym]
		data = self.query(query, params)
		# should only return 1 row right, if it exists
		avg_exists = data.fetchone()
		if(avg_exists != None):
			return avg_exists
		return -1

	def updateAverage(self, sym, price, vol, num):
		table = "averages_live"
		if(self.state != 1):
			table = "averages_static"
		query = "UPDATE " + table + \
			" SET averagePrice=?, averageVolume=?, numTrades=? WHERE symbol=?"
		params = [price, vol, num, sym]
		updated = self.action(query, params)
		#print("Total number of rows updated :", updated)
		if(updated == 0):  # check to see if it was updated
            # add row
			query = "INSERT INTO " + table + " VALUES (?,?,?,?)"
			params = [sym, price, vol, 0]
			updated = self.action(query, params)
		
	def addTransaction(self,data):
		if(isinstance(data, TradeData)):
			query = ""
			if(self.state == 1):
				query = "INSERT INTO trans_live VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
			else:
				query = "INSERT INTO trans_static VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
				params = (data.time, data.buyer, data.seller, data.price, data.size,
				data.currency, data.symbol, data.sector, data.bidPrice, data.askPrice)
				self.action(query, params)

				print(self.c.lastrowid)
				# Update the averages tables
				avgData = self.getAverage(data.symbol)
				if(avgData == -1):
					# No averages present
					self.updateAverage(data.symbol, data.price, data.size, 0)
					return

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
				return 0
		else:
			return -1

	def getTransactions(self, q):
		data = self.query(q)
		transactions = []
		for row in data:
			transactions.append(TradeData(row[0], row[1], row[2], row[3], row[
								4], row[5], row[6], row[7], row[8], row[9]))

		return transactions

	def clear(self, date):
		# delete all entries with the same date
		table = "trans_live"
		if(self.state == 1):
			table = "trans_static"

		query = "DELETE FROM " + table + " WHERE time=?"
		params = [date]
		self.action(query, params)
		return 0

	# gets all the anomalies for the table, returns a list of anomaly objects
	def getAnomalies(self, done):
		table = "anomalies_live"
		if(self.state != 1):
			table = "anomalies_static"  # shouldn't exist but for the sake of it
		query = "SELECT id,tradeid,category FROM " + table + " WHERE actiontaken=?"
		params = [done]
		data = self.query(query, params)
		rows = data.fetchall()
		anomalies = []
		for row in rows:
			# gonna get complicated
			# each row needs to do another sql query to get trade and turn into
			# TradeData
			table = "trans_live"
			if(self.state != 1):
				table = "trans_static"
			query = "SELECT time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + \
				table + " WHERE id=?"
			params = [row[1]]
			data = self.query(query, params)
			t = data.fetchone()
			trade = to_TradeData(t)
			a = Anomaly(row[0], trade, row[2])
			anomalies.append(a)
		return anomalies

	def addAnomaly(self, anomaly,tradeid):
		if(isinstance(anomaly, Anomaly)):
			table = "anomalies_live"
			if(self.state != 1):
				table = "anomalies_static"

			query = "INSERT INTO " + table + " VALUES(NULL, ?, ?, 0)"
			params = [tradeid, anomaly.category]
			self.action(query, params)
			return 1
		return -1

	def getAveragePrice(self, sym):
		return self.getAverage(sym)[1]

	def getAverageVolume(self, sym):
		return self.getAverage(sym)[2]
