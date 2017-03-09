import sqlite3, csv
from app import mtrade
from os.path import isfile, getsize
import os

from datetime import datetime, timedelta

class Database:

	def __init__(self, state=1):
		# check to see if db exists
		# if it doesn't then create it using schema
		filename = "database.db"
		if(not isfile(filename) or getsize(filename) < 100):
			# creating database
			self.conn = sqlite3.connect(filename)
			self.c = self.conn.cursor()
			with open('schema.sql') as fp:
				self.c.executescript(fp.read())  # or con.executescript
		else:
			self.conn = sqlite3.connect(filename)
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

	def readfile(self):
		with open('trades.csv','r') as csvfile:
			data_csv = csv.reader(csvfile, delimiter = ',')
			to_db = [(i[0],i[1],i[2],i[3],i[4],i[5],i[6],i[7],i[8],i[9]) for i in data_csv]
			print(to_db[0])
			self.c.executemany("INSERT INTO trans_static VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", to_db)
		self.conn.commit()
		print("done")

	def addTransactions(self,trades,state):
		#bulk add, only add when an anomaly is detected
		ttable = "trans_live"
		if(state!=1):
			ttable = "trans_static"
		tradeid=-1
		query = "INSERT INTO " + ttable + " VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
		for data in trades:
			params = (data.time, data.buyer, data.seller, data.price, data.size,
					  data.currency, data.symbol, data.sector, data.bidPrice, data.askPrice)
			self.c.execute(query, params)
			tradeid=self.c.lastrowid
	
		if(len(trades)>0):
			self.conn.commit()
		return tradeid
	
	def addTransaction(self,data, state):
		if(isinstance(data, mtrade.TradeData)):
			query = ""
			if(state == 1):
				query = "INSERT INTO trans_live VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
			else:
				query = "INSERT INTO trans_static VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
			tradeid=-1
			params = (data.time, data.buyer, data.seller, data.price, data.size,
			data.currency, data.symbol, data.sector, data.bidPrice, data.askPrice)
			self.action(query, params)

			tradeid=self.c.lastrowid
			# Update the averages tables
			#avgData = self.getAverage(data.symbol)
			#if(avgData == -1):
				# No averages present
				#self.updateAverage(data.symbol, data.price, data.size, 0)
				#return tradeid

			#avgPrice, avgVolume, numTrades = avgData[1], avgData[2], avgData[3]
			# Recalculate the averages
			#avgPrice *= numTrades
			#avgVolume *= numTrades
			#avgPrice += float(data.price)
			#avgVolume += int(data.size)
			#numTrades += 1
			#avgPrice /= numTrades
			##avgVolume /= numTrades
			#self.updateAverage(data.symbol, avgPrice, avgVolume, numTrades)
			return tradeid
		else:
			return -1

	def anomalycount(self,state):
		table = "anomalies_live"
		if(state!=1):
			table = "anomalies_static"
		return self.getcount(table,state)

	def tradecount(self,state):
		table = "trans_live"
		if(state!=1):
			table = "trans_static"
		return self.getcount(table,state)

	def getcount(self, table,state):
		query = "SELECT COUNT(*) FROM " + table
		params =[]
		data = self.query(query, params)
		t = data.fetchone()
		return t[0]

	def tradedetails(self,state):
		table = "trans_live"
		if(state!=1):
			table = "trans_static"
		query = "SELECT SUM(price * volume),COUNT(*) FROM "+table
		params = []
		data = self.query(query, params)
		t = data.fetchone()
		return t

	def getAveragePrice(self, sym):
		return self.getAverage(sym)[1]

	#def getAverageVolume(self, sym):
	#	return self.getAverage(sym)[2]
	#		query = "INSERT INTO " + table + " VALUES (?,?,?,?)"
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

		query = "DELETE FROM " + table + " WHERE time=?"
		params = [date]
		self.action(query, params)
		return 1
	
	def clearall(self,state):
		#delete all entries from trades and anomalies
		try:
			ttable = "trans_live"
			atable = "anomalies_live"
			if(state!=1):
				ttable = "trans_static"
				atable = "anomalies_static"
			query = "DELETE FROM " + ttable
			self.c.execute(query)
			query = "DELETE FROM " + atable
			self.c.execute(query)
			self.conn.commit()
		except:
			return False
		return True
		
	# gets all the anomalies for the table, returns a list of anomaly objects
	def getAnomalies(self, done,state):
		atable = "anomalies_live"
		ttable = "trans_live"
		if(state != 1):
			atable = "anomalies_static"
			ttable = "trans_static"
		query = "SELECT " +atable+".id,tradeid,category,time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + atable + " JOIN "+ttable+" ON "+ttable+ ".id="+atable+".tradeid WHERE actiontaken=?"
		params = [done]
		data = self.query(query, params)
		rows = data.fetchall()
		anomalies = []
		for row in rows:
			t = mtrade.to_TradeData(row[3:])
			a = mtrade.Anomaly(row[0], t, row[2])
			anomalies.append(a)
		return anomalies
	
	def getAnomalyById(self, id,state):
		# Useful function for the drill down stuff
		table1 = "anomalies_live"
		table2 = "trans_live"
		if(state != 1):
			table1 = "anomalies_static"
			table2 = "trans_static"
		query = "SELECT category,time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + table1 + " JOIN "+table2+" ON "+table2+ ".id="+table1+".tradeid WHERE "+table1+".id=?"
		params = [id]
		data = self.query(query, params)
		t = data.fetchone()
		category=t[0]
		trade = mtrade.to_TradeData(t[1:]) #remove category
		return mtrade.Anomaly(id, trade, category)

	def addAnomaly(self, tradeid, category, state):
		anomalyid = -1
		table = "anomalies_live"
		if(state != 1):
			table = "anomalies_static"

		query = "INSERT INTO " + table + " VALUES(NULL, ?, ?, 0)"
		params = [tradeid, category]
		self.action(query, params)
		anomalyid = self.c.lastrowid
		return anomalyid

	def getAveragePrice(self, sym):
		return self.getAverage(sym)[1]

	def getAverageVolume(self, sym):
		return self.getAverage(sym)[2]

	def getTradesForDrillDown(self, sym, time,state):
		# Return set of recent trades before and after anomaly
		# Get trade id
		ttable = "trans_live"
		if(state != 1):
			ttable = "trans_static"
		try:
			time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")
		except ValueError:
			time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
		upper = time + timedelta(hours=12) #create an upper and lower boundary frame TODO change if necessary
		lower = time - timedelta(hours=12)
		# Get trades beforehand
		query = "SELECT time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + \
			ttable + " WHERE(symbol=? AND datetime(time) BETWEEN datetime(?) AND datetime(?)) ORDER BY datetime(time) ASC"
		params = [sym, lower, upper]
		rows = self.query(query, params)
		trades = []
		for row in rows:
			trade = mtrade.to_TradeData(row)
			trades.append(trade)

		return trades
#this is not needed, + so stupid slow
	def getTradesByPerson(self,person,sym,state):
		trades = []
		table = "trans_live"
		if(state != 1):
			table = "trans_static"
		query = "SELECT time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM "+ table+ " WHERE(symbol=? AND (buyer=? OR seller=?)) ORDER BY datetime(time) ASC"
		params = [sym,person,person]
		rows = self.query(query, params)
		for row in rows:
			trade = mtrade.to_TradeData(row)
			trades.append(trade)
		return trades

	def dismissAnomaly(self,id,state):
		table = "anomalies_live"
		if(state != 1):
			table = "anomalies_static"
		query = "UPDATE "+table+ " SET actiontaken=1 WHERE id=?"
		params = [id]
		self.action(query,params)
		return 1
