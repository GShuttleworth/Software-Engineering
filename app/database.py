import mysql.connector
from app import mtrade
from os.path import isfile, getsize
import os

from datetime import datetime, timedelta

class Database:

	def __init__(self, state=1):
		# check to see if db exists
		# if it doesn't then create it using schema
		self.conn = mysql.connector.connect(user='root', password='andypandy', host='127.0.0.1', database='cs261')
		self.c = self.conn.cursor()
		self.state = state  # Default is 1 (live)
		self.currentId = 0
		self.startId = 0

	# General purpose functions
	def query(self, query, params):
		# for basic queries
		self.c.execute(query, params)
		return self.c.fetchall()

	def action(self, query, params):
		# for update, insert, etc
		if(self.state == 1):
			self.c.execute(query, params)
			self.conn.commit()
			return self.c.rowcount
		else:
			self.c.execute(i[0], i[1])
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
		query = "SELECT * FROM " + table + " WHERE symbol=%s"
		params = [sym]
		data = self.query(query, params)
		if(len(data) < 1):
			return -1
		# should only return 1 row right, if it exists
		avg_exists = data[0]
		if(avg_exists != None):
			return avg_exists
		return -1

	def updateAverage(self, sym, price, vol, num):
		table = "averages_live"
		if(self.state != 1):
			table = "averages_static"
		query = "UPDATE " + table + \
				" SET averagePrice=%s, averageVolume=%s, numTrades=%s WHERE symbol=%s"
		params = [price, vol, num, sym]
		updated = self.action(query, params)
		#print("Total number of rows updated :", updated)
		if(updated == 0):  # check to see if it was updated
			# add row
			query = "insert INTO " + table + " VALUES (%s,%s,%s,%s)"
			params = [sym, price, vol, 0]
			updated = self.action(query, params)

	def getFirstId(self):
		self.startId = self.query("select * from trans_static limit 1", [])[0][0] - 1 # Minus one so corresponding for correct trade
		print("first id is " + str(self.startId))

	def addTransaction(self,data, state):
		if(isinstance(data, mtrade.TradeData)):
			query = ""
			if(state == 1):
				query = "insert INTO trans_live VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
			else:
				return data.id
				
			tradeid=-1
			params = (data.time, data.buyer, data.seller, data.price, data.size,
			data.currency, data.symbol, data.sector, float(data.bidPrice), float(data.askPrice))
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
		t = data[0]
		return t[0]

	def tradedetails(self,state):
		table = "trans_live"
		if(state!=1):
			table = "trans_static"
		query = "SELECT SUM(price * volume),COUNT(*) FROM "+table
		params = []
		data = self.query(query, params)
		t = data[0]
		return t

	def getAveragePrice(self, sym):
		return self.getAverage(sym)[1]

	#def getAverageVolume(self, sym):
	#	return self.getAverage(sym)[2]
	#		query = "insert INTO " + table + " VALUES (%s,%s,%s,%s)"
	#		params = [sym, price, vol, 0]
	#		updated = self.action(query, params)

	def getTransactions(self, q):
		data = self.query(q, [])
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

		query = "DELETE FROM " + table + " WHERE time=%s"
		params = [date]
		self.action(query, params)
		return 1
	
	def clearall(self,state):
		#delete all entries from trades and anomalies
		try:
			table = "trans_live"
			if(state==0):
				table = "trans_static"
			query = "DELETE FROM " + table
			params = []
			self.action(query, params)
			table = "anomalies_live"
			if(state==0):
				table = "anomalies_static"
			query = "DELETE FROM " + table
			params = []
			self.action(query, params)
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
		query = "SELECT " +atable+".id,tradeid,category,time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + atable + " JOIN "+ttable+" ON "+ttable+ ".id="+atable+".tradeid WHERE actiontaken=%s"
		params = [done]
		rows = self.query(query, params)
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
		query = "SELECT category,time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + table1 + " JOIN "+table2+" ON "+table2+ ".id="+table1+".tradeid WHERE "+table1+".id=%s"
		params = [id]
		data = self.query(query, params)
		t = data[0]
		category=t[0]
		trade = mtrade.to_TradeData(t[1:]) #remove category
		return mtrade.Anomaly(id, trade, category)

	def addAnomaly(self, tradeid, category, state):
		anomalyid = -1
		table = "anomalies_live"
		if(state != 1):
			table = "anomalies_static"
		
		query = "insert INTO " + table + " VALUES(NULL, %s, %s, 0)"
		params = [tradeid, category]
		'''
		if(state == 0):
			params = [self.currentId + self.query("select * from trans_static limit 1", [])[0][0] - 1, category]
			print("params are " + str(params))
			'''
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
		upper = time + timedelta(hours=6) #create an upper and lower boundary frame TODO change if necessary
		lower = time - timedelta(hours=6)
		# Get trades beforehand
		query = "SELECT time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + \
			ttable + " WHERE(symbol=%s AND unix_timestamp(time) BETWEEN unix_timestamp(%s) AND unix_timestamp(%s)) ORDER BY unix_timestamp(time) ASC"
		params = [sym, lower, upper]
		rows = self.query(query, params)
		trades = []
		for row in rows:
			trade = mtrade.to_TradeData(row)
			trades.append(trade)

		return trades

	def addAnomalyStatic(self, trade, category):
		if(isinstance(trade, mtrade.TradeData)):
			query = "insert into anomalies_static values(NULL, (SELECT id FROM trans_static WHERE time=%s and buyer=%s and seller=%s and price=%s and symbol=%s), %s, 0)"
			params = [trade.time,trade.buyer,trade.seller,trade.price,trade.symbol,category]
			self.action(query, params)
			anomalyid = self.c.lastrowid
			return anomalyid
		return -1

	def getTradesByPerson(self, person, sym, state):
		trades = []
		table = "trans_live"
		if(state != 1):
			table = "trans_static"
		query = "SELECT time,buyer,seller,price,volume,currency,symbol,sector,bidPrice,askPrice FROM " + table+ " WHERE(symbol=%s AND (buyer=%s OR seller=%s)) ORDER BY unix_timestamp(time) ASC"
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
		query = "UPDATE "+table+ " SET actiontaken=1 WHERE id=%s"
		params = [id]
		self.action(query,params)
		return 1

	



