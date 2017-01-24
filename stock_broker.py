from yahoo_finance import Share
from collections import namedtuple, OrderedDict
from random import choice, sample, shuffle
import time
from datetime import datetime, timedelta
import csv
import get_stock_list
import subprocess
import pandas as pd
from text_generator import Text_Generator as tg



######################
## Data Structures

Account = namedtuple('Client', 'num, name, portfolio, funds, watchlist, history')
Holding = namedtuple('Holding', 'holding, price')
Forecast = namedtuple('Forecast', 'stock, date, base_price, prediction')
data_file = 'accounts.csv'
predictions_file = 'predictions.csv'


######################
## Broker Class

class Broker():

    def __init__(self):
        try:
            with open(data_file, 'r') as f:
                reader = csv.DictReader(f)
                file_data = [Account(**row) for row in reader]
        except FileNotFoundError:
            file_data = []
        try:
            with open(predictions_file, 'r') as f:
                reader = csv.DictReader(f)
                self.predictions = [Forecast(**row) for row in reader]
        except FileNotFoundError:
            self.predictions = []
        self.accounts = {client.num: client for client in file_data}
        self.account_num = len(file_data)
        self.predictions = {p.stock: p for p in self.predictions}
        print("loaded predictions:", self.predictions)
        self.tip = tg.tip_of_the_day()
        for account in self.accounts:
            self.accounts[account] = Account(self.accounts[account].num, self.accounts[account].name,
                                     eval(self.accounts[account].portfolio), float(self.accounts[account].funds),
                                     eval(self.accounts[account].watchlist), eval(self.accounts[account].history))
        print("loaded data")

    def open_account(self, name):
        self.account_num += 1
        num = self.account_num + 1000
        new_account = Account(num, name, {}, 0, {}, [])
        self.accounts[str(num)] = new_account
        print("account opened.")
        print("account name:", name)
        print("account number:", num)

    def check_balance(self, num):
        try:
            account = self.accounts[num]
            current_balance = float(account.funds)
            print('current balance: ' + str(current_balance))
        except KeyError:
            print('account not found')
        try:
            value = self.get_value(account)
            print("current value of stocks:", value)
        except Exception:
            print("could not retrieve value of portfolio")

    def add_funds(self, num, funds):
        if (type(funds) == int or type(funds) == float) and \
                (funds > 0 and funds < 10 ** 9):
            try:
                account = self.accounts[num]
                current_balance = float(account.funds)
                print('current balance: ' + str(current_balance))
            except KeyError:
                print('account not found')
            else:
                new_balance = current_balance + funds
                print('new balance:' + str(new_balance))
                account.history.append([datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), "credit " \
                                        + str(funds) + ': ' + str(new_balance)])
                new_account = Account(num, account.name, account.portfolio, new_balance,
                                      account.watchlist, account.history)
                self.accounts[num] = new_account
        self.save_accounts()

    def update_portfolio(self, num):
        print(datetime.now(), 'update_portfolio')
        try:
            account = self.accounts[num]
            current_balance = account.funds
            print('current balance: ' + str(current_balance))
            print("portfolio:", account.portfolio)
        except KeyError:
            print('account not found')
        else:
            self.refresh_predictions()
            actions = self.review_portfolio(account)
            new_account, comment1 = self.predictive_buy(account)
            new_account, comment2 = self.sell_stocks(new_account, actions)
            self.accounts[num] = new_account
            return comment1, comment2

    def get_value(self, account):
        portfolio = account.portfolio
        value = 0
        for stock in portfolio.keys():
            try:
                s = Share(stock)
                current_price = s.get_price()
                current_value = portfolio[stock].holding * float(current_price)
                value += current_value
            except Exception: return "problem retrieving current prices"
        return value

    def get_risers_and_fallers(self, account):
        print(datetime.now(), 'checking risers and fallers')
        risers = []
        fallers = []
        if account.portfolio != {}:
            for key in account.portfolio.keys():
                try:
                    share = account.portfolio[key]
                    bought_price = float(share.price)
                    units = float(share.holding)
                    total_bought_price = bought_price * units
                    s = Share(key)
                    price = float(s.get_price())
                    net_gain = round((price * units) - total_bought_price, 2)
                    print("net", net_gain)
                    percent_gain = round(((price - bought_price) / bought_price) * 100, 2)
                    print("percent", percent_gain)
                    if percent_gain > 0:
                        risers.append((key, percent_gain, net_gain))
                    else:
                        fallers.append((key, percent_gain, net_gain))
                except:
                    continue
        return risers, fallers

    def review_portfolio(self, account):
        print(datetime.now(), 'review_portfolio')
        value = self.get_value(account)
        print('current stock value:', value)
        print('current cash:', account.funds)
        try:
            total_value = float(value) + account.funds
            threshold = total_value / 10 # don't hold more than the threshold in any stock
            print('current total value:', str(value + account.funds))
        except Exception as e:
            print(e)
            threshold = 0
        actions = {'buy': 0, 'sell': []}
        if float(account.funds) > 500:
            actions['buy'] = 1
        sell_shares = []
        if account.portfolio != {}:
            for key in account.portfolio.keys():
                try:
                    forecast = self.predictions[key]
                    if forecast.prediction == '-1':
                        sell_shares.append(key)
                except Exception as e:
                    print(e)
        if len(sell_shares) > 0:
            actions['sell'] = sell_shares
        print("looking to sell")
        for share in sell_shares:
            print(share)
        return actions

    def sell_stocks(self, account, actions):
        print(datetime.now(), 'sell_stocks')
        if actions['sell'] == []: return account, ''
        portfolio = account.portfolio
        total_proceeds = 0
        sell_statement = []
        for stock in actions['sell']:
            try:
                s = Share(stock)
                current_price = float(s.get_price())
            except Exception:
                print("network error: cannot process transaction for", stock, ". Try again later")
                return account, ''
            else:
                holding = portfolio[stock]
                units_to_sell = holding.holding
                proceeds = current_price * units_to_sell
                total_proceeds += proceeds
                total_cost = units_to_sell * holding.price
                profit = round(proceeds - total_cost, 2)
                print("sold", units_to_sell, "of", stock, "at", current_price)
                print("profit: ", profit)
                sell_statement.append((stock, profit))
                portfolio.pop(stock, None)
                account.history.append([datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), 'sold ' \
                                        + str(units_to_sell) + ' ' + stock + '(' + str(profit) + ')' \
                                        + ': ' + str(float(account.funds) + proceeds)])
            new_account = Account(account.num, account.name, portfolio, account.funds + total_proceeds,
                                  account.watchlist, account.history)
        sell_statement_stocks = [s for (s, p) in sell_statement]
        sell_statement_profit = sum([profit for (s, profit) in sell_statement])
        if sell_statement_stocks == []:
            sell_statement = ''
        else:
            sell_statement = 'sold ' + str(sell_statement_stocks) + ' . total profit: ' + str(sell_statement_profit)
        return new_account, sell_statement

    def predictive_buy(self, account):
        print(datetime.now(), 'predictive_buy')
        today = datetime.strftime(datetime.now(), '%Y-%m-%d')
        print("all predictions on file:", self.predictions)
        try:
            risers = [f.stock for f in self.predictions.values() if f.prediction == '1']
            fallers = [f.stock for f in self.predictions.values() if f.prediction == '-1']
            print("broker forecasts - risers:", risers)
            print("broker forecasts - fallers:", fallers)
        except Exception as e:
            print(e)
            return self.buy_stocks(account, {'buy': 0}, [])
        account, buy_statement = self.buy_stocks(account, {'buy': 1}, [x for x in risers])
        return account, buy_statement

    def buy_stocks(self, account, actions, buy_list):
        funds = float(account.funds) / 3
        remaining_funds = float(account.funds) - funds
        if actions['buy'] == 0:
            return account, 'nothing caught my eye'
        elif funds < 900:
            return account, "i'm skint"
        value = self.get_value(account)
        try:
            total_value = float(value) + account.funds
            threshold = (total_value / 10) - 500 # don't hold more than threshold amount of any given stock
        except Exception as e:
            print(e)
            threshold = 7500

        # buy shares
        portfolio = account.portfolio
        if buy_list == []:
            return account, "nothing caught my eye"
        buy_statement = ''
        shuffle(buy_list)
        for stock in buy_list:
            try:
                s = Share(stock)
                current_price = float(s.get_price())
            except Exception:
                print("network error: could not process transaction for", stock)
                return account, 'network error'
            num_shares = int((funds / 5) / current_price)
            if num_shares < 1:
                continue
            elif stock in portfolio.keys() and (portfolio[stock].holding * portfolio[stock].price) > threshold:
                continue
            else:
                funds -= num_shares * current_price
                if stock in portfolio.keys():
                    holding = portfolio[stock]
                    current_holding = holding.holding
                    current_av_price = holding.price
                else:
                    current_holding = 0
                    current_av_price = 0
                current_total_price = current_av_price * current_holding
                current_holding += num_shares
                current_av_price = (current_total_price + (num_shares *
                                                        current_price)) / current_holding
            holding = Holding(current_holding, current_av_price)
            portfolio[stock] = holding
            buy_statement = "bought " + stock + " at " + str(current_price)
            account.history.append([datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), 'bought ' \
                                   + str(num_shares) + ' ' + stock + ': ' + str(funds)])
        funds += remaining_funds
        new_account = Account(account.num, account.name, portfolio, funds, account.watchlist, account.history)
        return new_account, buy_statement

    def get_predictions(self, predictions):
        for p in predictions:
            print(p)
            f = Forecast(p[0], p[1], p[2], p[3])
            self.predictions[p[0]] = f
        print(self.predictions)
        self.refresh_predictions()
        self.save_accounts()

    def refresh_predictions(self):
        yesterday = datetime.now() - timedelta(days=2)
        self.predictions = {k: v for k, v in self.predictions.items() if datetime.strptime(v.date, '%Y-%m-%d') >=
                            yesterday}

    def save_accounts(self):
        accounts = self.accounts
        preds = self.predictions
        print("saving")
        with open(data_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(('num', 'name', 'portfolio', 'funds', 'watchlist', 'history'))
            writer.writerows([(accounts[client].num, accounts[client].name, accounts[client].portfolio,
                               accounts[client].funds, accounts[client].watchlist, accounts[client].history)
                               for client in accounts])
        with open(predictions_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(('stock', 'date', 'base_price', 'prediction'))
            writer.writerows([(p.stock, p.date, p.base_price, p.prediction) for p in preds.values()])
        

    @property
    def tip(self):
        return self._tip

    @tip.setter
    def tip(self, stock):
        self._tip = stock
        print("setting tip:", self.tip)



if __name__ == '__main__':
    b = Broker()
    while True:
        b.manage_accounts()
        time.sleep(600)
