from flask import render_template
from app import app
from flask import request
import sys
sys.path.append(".")
from app import mtrade
from app import database
from app import dbm

from datetime import datetime, timedelta

@app.route('/')
@app.route('/index')
def index():
    pagename = "Dashboard"
    livedata = True
    numberOfAnomalies = "Loading..."
    numberOfTrades = "Loading..."
    totalTradeValue = "Loading..."
    # what is this??? A: The ID assigned to each anomaly, increment by 1 for
    # eachndetected
    anomalyID = 1
    anomalyDate = "Timestamp"
    anomalyType = "Pump and Dump"
    return render_template('dashboard.html', pagename=pagename, numberOfAnomalies=numberOfAnomalies, numberOfTrades=numberOfTrades, totalTradeValue=totalTradeValue, livedata=livedata)


@app.route('/stock', methods=['GET', 'POST'])
@app.route('/stock/<symbol>/anomaly/<id>', methods=['GET', 'POST'])
def anomaly(symbol, id):
	# Create database instancea
	db = database.Database()
	state=1
	anomaly = db.getAnomalyById(id,state)

	baseTrade = anomaly.trade
	trades = db.getTradesForDrillDown(baseTrade.symbol, baseTrade.time,state)
	#??for t in trades:
	#    t.time = t.time[10:19]
	db.close() # Close quickly to prevent any issues
	return anomaly_template(trades,baseTrade,symbol,id)

@app.route('/static/stock', methods=['GET', 'POST'])
@app.route('/static/stock/<symbol>/anomaly/<id>', methods=['GET', 'POST'])
	# Create database instance
def static_anomaly(symbol,id):
	db = database.Database()
	state=0
	anomaly = db.getAnomalyById(id,state)
	baseTrade = anomaly.trade
	trades = db.getTradesForDrillDown(baseTrade.symbol, baseTrade.time,state)
	db.close() # Close quickly to prevent any issues
	return anomaly_template(trades,baseTrade,symbol,id)

def anomaly_template(trades,baseTrade,symbol,id):
	trades=trades
	pagename = "Anomaly Information for " + symbol
	anomalyType = "TODO"
	anomalyStartTimestamp = "TODO"
	anomalyEndTimestamp = "TODO"
	certantyPercentage = "TODO"
	time = baseTrade.time
	buyer = baseTrade.buyer
	seller = baseTrade.seller
	price = baseTrade.price
	size = baseTrade.size
	currency = baseTrade.currency
	symbol = baseTrade.symbol
	sector = baseTrade.sector
	bid = baseTrade.bidPrice
	ask = baseTrade.askPrice
	date = convert_date(time).strftime("%A, %d %B %Y")
	rangetime = convert_date(time)
	first = convert_date(trades[0].time)
	last = convert_date(trades[len(trades)-1].time)
	lower = max(first,rangetime - timedelta(minutes=15)) #create an upper and lower boundary frame TODO change if necessary
	upper = min(last,rangetime + timedelta(minutes=15))
	return render_template('anomaly.html', **locals())

def convert_date(time):
	try:
		time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")
	except ValueError:
		time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
	return time
@app.route('/', methods=['POST'])
def my_form_post():
    pagename = "Home"
    text = request.form['text']
    print(text)
    return render_template('index.html', pagename=pagename)
