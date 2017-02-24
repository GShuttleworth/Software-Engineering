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
	
	def reset(self):
		# Deletes all enteries to reset db
		#TODO
		return 0
	
	def getAveragePrice(self, sym):
		avg = -1 #sanity check!
		table = "running_price_avg_live"
		if(self.state != 1):
			table = "running_price_avg_static"
		
		query = "SELECT averagePrice FROM " + table + " WHERE symbol=?"
		params = [sym]
		data = self.query(query,params)
		#should only return 1 row right, if it exists
		avg_exists = data.fetchone()
		if(avg_exists):
			avg=avg_exists
		return avg

	def updateAveragePrice(self, sym, val):
		#attempts to update
		table = "running_price_avg_live"
		if(self.state != 1):
			table = "runnning_price_avg_static"
		query = "UPDATE " + table + " SET averagePrice=? WHERE symbol=?"
		params = [val,sym]
		updated = self.action(query,params)
		#print("Total number of rows updated :", updated)
		if(updated==0): #check to see if it was updated
			#add row
			query = "INSERT INTO " + table + " VALUES (?,?)"
			params = [sym,val]
			updated = self.action(query,params)
		
	def updateDaily(self, date, sym, avg, table):
		query = "INSERT INTO " + table + " VALUES(?,?,?)"
		params = [sym,avg,date]
		self.action(query, params)

	def getDaily(self, date, sym, table):
		# Assumes average is set at 00:00 and not changed again
		avg = -1
		query = "SELECT * FROM " + table + " WHERE(dateRecorded=? AND symbol=?)"
		params = [date, sym]
		data = self.query(query, params)
		# Should only be one record per day
		avg_exists = data.fetchone()
		if(avg_exists):
			avg = avg_exists
		return avg

	def updatePriceDaily(self, date, sym, avg):
		if(self.state == 1):
			self.updateDaily(date, sym, avg, "daily_price_avg_live")
		else:
			self.updateDaily(date, sym, avg, "daily_price_avg_static")

	def updateVolumeDaily(self, date, sym, avg):
		if(self.state == 1):
			self.updateDaily(date, sym, avg, "daily_volume_avg_live")
		else:
			self.updateDaily(date, sym, avg, "daily_volume_avg_static")

	def getPriceDaily(self, date, sym):
		if(self.state == 1):
			return self.getDaily(date, sym, "daily_price_avg_live")
		else:
			return self.getDaily(date, sym, "daily_price_avg_static")

	def getVolumeDaily(self, date, sym):
		if(self.state == 1):
			return self.updateDaily(date, sym, "daily_volume_avg_live")
		else:
			return self.updateDaily(date, sym, "daily_volume_avg_static")

	def updateDaily(self, date, sym, avg, table):
		query = "INSERT INTO " + table + " VALUES(?,?,?)"
		params = [sym,avg,date]
		self.action(query, params)

	def getDaily(self, date, sym, table):
		# Assumes average is set at 00:00 and not changed again
		avg = -1
		query = "SELECT * FROM " + table + " WHERE(dateRecorded=? AND symbol=?)"
		params = [date, sym]
		data = self.query(query, params)
		# Should only be one record per day
		avg_exists = data.fetchone()
		if(avg_exists):
			avg = avg_exists
		return avg

	def updatePriceDaily(self, date, sym, avg):
		if(self.state == 1):
			self.updateDaily(date, sym, avg, "daily_price_avg_live")
		else:
			self.updateDaily(date, sym, avg, "daily_price_avg_static")

	def updateVolumeDaily(self, date, sym, avg):
		if(self.state == 1):
			self.updateDaily(date, sym, avg, "daily_volume_avg_live")
		else:
			self.updateDaily(date, sym, avg, "daily_volume_avg_static")

	def getPriceDaily(self, date, sym):
		if(self.state == 1):
			return self.getDaily(date, sym, "daily_price_avg_live")
		else:
			return self.getDaily(date, sym, "daily_price_avg_static")

	def getVolumeDaily(self, date, sym):
		if(self.state == 1):
			return self.updateDaily(date, sym, "daily_volume_avg_live")
		else:
			return self.updateDaily(date, sym, "daily_volume_avg_static")
