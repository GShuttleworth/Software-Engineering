from flask import render_template
from app import app
from flask import request
import sys
sys.path.append(".")
from app import mtrade
from app import database
from app import dbm

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
    global dbm
    print("state is " + str(dbm.mode))
    db = database.Database(dbm.mode)
    print("state is" + str(db.state))
    anomaly = db.getAnomalyById(id)
    baseTrade = anomaly.trade
    trades = db.getTradesForDrillDown(baseTrade.symbol, id)
    for t in trades:
        t.time = t.time[10:19]
    db.close() # Close quickly to prevent any issues
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
    return render_template('anomaly.html', **locals())


@app.route('/', methods=['POST'])
def my_form_post():
    pagename = "Home"
    text = request.form['text']
    print(text)
    return render_template('index.html', pagename=pagename)
