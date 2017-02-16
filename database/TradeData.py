class TradeData:
	def __init__(self, time, buyer, seller, p, s, currency, symbol, sector, bidP, askP):
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
