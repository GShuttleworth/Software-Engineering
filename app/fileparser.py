class FileThread (threading.Thread):
	def __init__(self,threadID):
		threading.Thread.__init__(self)
		self.name = "File parser thread"
	def run(self):
		print("Starting file parsing thread")
		self.prepare()
		self.parsefile()
	
	def prepare():
		#needs to clear current queue and reset counters
		global _qlock
		global _q
		global _tradecounter
		global _anomalycounter
		global _tradevalue
		disconnect_stream()
		_qlock.acquire()
		_q.clear()
		_qlock.release()
		_tradecounter=0
		_anomalycounter=0
		_tradevalue=0
	
	def parsefile():
		#read file
		with open('trades.csv', 'r') as csvfile:
			
			reader = csv.reader(csvfile, delimiter = ',')
			
			for row in reader:
				if row[0] == 'time':
					continue
				else:
					_q.put(mtrade.to_TradeData(row))
