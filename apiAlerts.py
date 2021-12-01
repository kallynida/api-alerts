import argparse
import requests
import statistics
import time
import json
from datetime import datetime
from decimal import Decimal


# Price Deviation - Generate an alert if the current price is more than one standard deviation from the 24hr average

SYMBOLS_API = 'https://api.gemini.com/v1/symbols'
TICKER_API = 'https://api.gemini.com/v2/ticker/'

DEFAULT_DEVIATION = 1

parser = argparse.ArgumentParser(description='Generate gemini alerts')
parser.add_argument('-c', '--currency', help='Curreny trading pair')
parser.add_argument('-d', '--deviation', help='Percentage threshold for deviation')
args = parser.parse_args()

currency = args.currency
deviation = Decimal(args.deviation) if args.deviation else DEFAULT_DEVIATION 


def generateAlerts():
    symbols = _getSymbols()
    if currency:
        _generateAlertForSymbol(currency)
        return
    for symbol in symbols:
        _generateAlertForSymbol(symbol)
        time.sleep(1) # Throttle calls to ticket api

def _generateAlertForSymbol(symbol):
    try:
        response = requests.get(TICKER_API + symbol)
        tickerData = response.json()
        if not tickerData.get('changes'):
            return
        changes = [Decimal(price) for price in tickerData.get('changes')]
        avgPrice, stdDeviation = statistics.mean(changes), statistics.stdev(changes)
        lastPrice = Decimal(tickerData['close'])

        if stdDeviation:
            lastPriceDeviation = abs(lastPrice - avgPrice)/stdDeviation
        elif lastPrice - avgPrice != 0:
            lastPriceDeviation = float('inf')
        else:
            lastPriceDeviation = 0
        
        # Not clear on what deviation as a notional value means. Calculating it as the absolute diff of last price from mean.
        changeValue = abs(lastPrice - avgPrice)
        
        if lastPriceDeviation > deviation:
            print(_createAlert(symbol, 'INFO', avgPrice, changeValue, lastPriceDeviation, lastPrice))
    except Exception as e:
        print(_createAlert(symbol, 'ERROR', '', '', '', ''))


def _createAlert(symbol, level, avgPrice, changeValue, lastPriceDeviation, lastPrice):
    alert = {}
    alert['timestamp'] = datetime.now().isoformat()
    alert['level'] = level
    alert['trading_pair'] = symbol
    data = {}
    data['last_price'] = str(lastPrice)
    data['average'] = str(avgPrice)
    data['change'] = str(changeValue)
    data['sdev'] = str(lastPriceDeviation)
    alert['data'] = data
    return json.dumps(alert)
 
def _getSymbols():
    response = requests.get(SYMBOLS_API)
    return response.json()


if __name__ == "__main__":
    generateAlerts()
