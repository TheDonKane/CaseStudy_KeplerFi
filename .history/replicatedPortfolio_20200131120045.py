# Libraries
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pandas_datareader.data as data
import seaborn as sns
import datetime
import json
from yahoofinancials import YahooFinancials
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
import re
import requests
import warnings

driver = webdriver.Chrome()

asset_dict = {} 

warnings.filterwarnings('ignore')


def get_table(soup):
    for t in soup.select('table'):
        header = t.select('thead tr th')
        if len(header) > 2:
            if (header[0].get_text().strip() == 'Symbol'
                and header[2].get_text().strip().startswith('% Holding')):
                return t
    raise Exception('could not find symbol list table')
    
# Scrapes ETF holdings from barchart.com
def get_etf_holdings():
    '''
    etf_symbol: str
    
    return: pd.DataFrame
    '''
    url = 'https://www.barchart.com/stocks/quotes/VONE/constituents?page=all'

    # Loads the ETF constituents page and reads the holdings table
    browser = WebDriver() # webdriver.PhantomJS()
    browser.get(url)
    html = browser.page_source
    soup = BeautifulSoup(html, 'html')
    table = get_table(soup)

    # Reads the holdings table line by line and appends each asset to a
    # dictionary along with the holdings percentage
    for row in table.select('tr')[1:26]:
        try:
            cells = row.select('td')
            # print(row)
            symbol = cells[0].get_text().strip()
            # print(symbol)
            # name = cells[1].text.strip()
            celltext = cells[2].get_text().strip()
            percent = float(celltext.rstrip('%'))
            # shares = int(cells[3].text.strip().replace(',', ''))
            if symbol != "" and percent != 0.0:
                asset_dict[symbol] = {
                    'percent': percent,
                }
        except BaseException as ex:
            print(ex)
    browser.quit()
    return pd.DataFrame(asset_dict)

constituent = get_etf_holdings()

constituent.T

# Assets
russell_index = ["^RUI"]
tickers = []

# Set timeframe
start = "2019-03-31"
end = "2019-04-29"


def pullTickers():

    list(asset_dict.keys())

    for key in asset_dict.keys():
        tickers.append(key.replace('.','-'))
    return tickers


pullTickers()

marketCaps = {}

def pullFundamentals():

    for i in tickers:
        yahoo_financials = YahooFinancials(i)
        sharesOutstanding = yahoo_financials.get_key_statistics_data()[i]['sharesOutstanding']
        
        prices = yahoo_financials.get_historical_price_data('2019-04-01', '2019-04-02', 'daily')[i]['prices'][0]['adjclose']

        mcap = sharesOutstanding * prices

        marketCaps[i] = mcap
        
        print(marketCaps)

pullFundamentals()

replicatedWeights = {}

aggregateValue = sum(marketCaps.values())    

for i in tickers:
    weights = marketCaps[i] / aggregateValue

    replicatedWeights[i] = weights

    print(replicatedWeights)
    
rweights = list(replicatedWeights.values())

print(rweights)


def replicateETF():
    prices = data.DataReader(tickers, data_source="yahoo", start=start, end=end)['Adj Close']
    x = 0
    for i in tickers:
        prices[i] *= rweights[x]
        x += 1

    prices['ETF'] = prices.sum(axis = 1)
    
    return prices['ETF']

replicateETF()

etfReturn = replicateETF().pct_change()[1:]


print(etfReturn)

def russell():
    # Pull data from Yahoo! Finance for Russell 1000 Index
    df = data.DataReader(russell_index, data_source="yahoo", start=start, end=end)

    #percentage = df["Adj Close"].pct_change()
    #russellReturn = percentage[1:]    

    return df["Adj Close"]


russell()

russellReturn = russell().pct_change()[1:]


russellTotalReturn = russellReturn.values.flatten()


print(russellTotalReturn)


def trackingError():

    returnDifference = etfTotalReturn - russellTotalReturn
    
    squaredValues = returnDifference ** 2

    sumation = squaredValues.sum()

    Error = (sumation / (20 - 1)) ** (1/2)


    print("Tracking Error is " + "{:.2%}".format(Error))


trackingError()

# create figure and axis objects with subplots()
fig,ax = plt.subplots()
# make a plot
fig.suptitle('Daily Adj Closing Price', fontsize=16)
plt.rcParams['figure.figsize'] = (12,8)
ax.plot(figsize = (12,8))
ax2.plot(figsize = (12,8))
ax.plot(replicateETF(), color="red", marker="o")
# set x-axis label
ax.set_xlabel("Date")
# set y-axis label
ax.set_ylabel("Replicated PF",color="red",fontsize=14)
ax2=ax.twinx()
ax2.plot(russell(), color="blue", marker="o")
ax2.set_ylabel("^RUI",color="blue",fontsize=14)
plt.show()

fig=plt.figure(figsize = (12,8))
fig.suptitle('Daily Returns', fontsize=16)

fig.show()
ax=fig.add_subplot(111)

plt.plot(russellTotalReturn, color="blue")
plt.plot(etfTotalReturn, color="red")

ax.set_ylabel("Return %",fontsize=14)
ax.set_xlabel("Days",fontsize=14)


