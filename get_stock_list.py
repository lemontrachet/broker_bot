from bs4 import BeautifulSoup
import requests
import re
from random import sample
from yahoo_finance import Share

##################################
## list of stocks

try:
    w = requests.get('https://uk.finance.yahoo.com/q/cp?s=%5EFTSE')
    w1 = requests.get('https://uk.finance.yahoo.com/q/cp?s=%5EFTSE&c=1')
    w2 = requests.get('https://uk.finance.yahoo.com/q/cp?s=%5EFTSE&c=2')
    soup = BeautifulSoup(w.text, 'html5lib')
    soup1 = BeautifulSoup(w1.text, 'html5lib')
    soup2 = BeautifulSoup(w2.text, 'html5lib')
    p = re.compile('/q\?s=(\w+.\w*)')
    table = soup.find("table", { "class" : "yfnc_tableout1" })
    table1 = soup1.find("table", { "class" : "yfnc_tableout1" })
    table2 = soup2.find("table", { "class" : "yfnc_tableout1" })

except Exception as e:
    print(e)
    pass

def get_stock_names(table):
    stocks = []
    for row in table.find_all("tr"):
        try:
            stock = re.search(p, str(row)).group(1)
            stocks.append(stock)
        except Exception: pass
    return stocks

def get_stocks():
    try:
        with open('stocks.txt', 'r') as f:
            tmp = f.read()
            assert len(tmp) > 10
            stocks = tmp.split()
            print("retrieving local stocks list")
        f.close()
        return stocks

    except Exception:
        print("retrieving stocks list from yahoo finance")
        try:
            tables = [table, table1, table2]
            stocks = [get_stock_names(t) for t in tables]
            print(stocks)
            stocks = [stock for tranche in stocks for stock in tranche]

            with open('stocks.txt', 'w') as f:
                for s in stocks:
                    f.write(str(s))
                    f.write(' ')
            f.close()
        except Exception as e:
            print(e)
            return []
        
    return stocks

if __name__ == '__main__':
    print(get_stocks())
