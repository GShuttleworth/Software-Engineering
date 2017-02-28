from flask import render_template
from app import app

from flask import request

@app.route('/')
@app.route('/index')
def index():
	pagename = "Dashboard"
	livedata = True
	numberOfAnomalies = "Loading..."
	numberOfTrades = "Loading..."
	totalTradeValue = "Loading..."
	#what is this??? A: The ID assigned to each anomaly, increment by 1 for eachndetected
	anomalyID = 1
	anomalyDate = "Timestamp"
	anomalyType = "Pump and Dump"
	return render_template('dashboard.html',pagename=pagename, numberOfAnomalies=numberOfAnomalies, numberOfTrades=numberOfTrades,totalTradeValue=totalTradeValue, livedata=livedata)

@app.route('/stock', methods=['GET','POST'])
@app.route('/stock/<symbol>/anomaly/<id>', methods=['GET','POST'])
def anomaly(symbol,id):
	pagename = "Anomaly Information for " + symbol
	anomalyType = "Pump and Dump"
	anomalyStartTimestamp = "timestamp"
	anomalyEndTimestamp = "timestamp"
	certantyPercentage = "52"
	time = "time"
	buyer = "buyer"
	seller = "seller"
	price = "50"
	size = "100"
	currency = "GBP"
	symbol = "DOLLA"
	sector = "sector"
	bid = "bid"
	ask = "ask"
	return render_template('anomaly.html', pagename=pagename)



@app.route('/', methods=['POST'])
def my_form_post():
	pagename = "Home"
	text = request.form['text']
	print(text)
	return render_template('index.html', pagename=pagename)