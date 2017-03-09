import inspect #validation TODO

class TradeData:
	def __init__(self, time, buyer, seller, p, s, currency, symbol, sector, bidP, askP, id=0):
		self.time = time
		self.buyer = buyer
		self.seller = seller
		self.price = p
		self.size = s
		self.currency = currency
		self.symbol = symbol
		self.sector = sector
		self.bidPrice = bidP
		self.askPrice = askP
		self.id = id

#parse from whole string
def parse(string):
	#will assume that it's already parsed so string = 1 string
	s = string.split(",") #splits string with , as delimiter, returns list
	return to_TradeData(s)

#input trade in list form
def to_TradeData(s):
	#s is a list
	return TradeData(s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9])

#anomaly class
class Anomaly:
	#trade is an instance of TradeData
	def __init__(self,id,trade,category):
		self.id = id
		self.trade = trade
		self.category = category
