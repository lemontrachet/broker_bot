from yahoo_finance import Share
from collections import namedtuple, OrderedDict
from random import choice, sample, shuffle
import time
from datetime import datetime, timedelta
import csv
import get_stock_list
from business_hours import market_open, time_until_open
import subprocess
import pandas as pd
from stock_predictor import Price_Predictor

######################
## Data Structures

Account = namedtuple('Client', 'num, name, portfolio, funds, watchlist, history')
Holding = namedtuple('Holding', 'holding, price')
data_file = 'accounts.csv'
forecast_file = 'predictions.csv'


######################
## Broker Class

class Broker():

    forecasts = pd.read_csv(forecast_file)

    def __init__(self):
        try:
            with open(data_file, 'r') as f:
                reader = csv.DictReader(f)
                file_data = [Account(**row) for row in reader]
            f.close()
        except FileNotFoundError:
            file_data = []

        self.accounts = {client.num: client for client in file_data}
        self.account_num = len(file_data)
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

    def update_portfolio(self, num, p=0):
        print(datetime.now(), 'update_portfolio')
        try:
            account = self.accounts[num]
            current_balance = account.funds
            print('current balance: ' + str(current_balance))
            print("portfolio:", account.portfolio)
        except KeyError:
            print('account not found')
        else:
            actions = self.review_portfolio(account)
            new_account, comment1 = self.buy_stocks(account, actions) if p == 1 else self.predictive_buy(account)
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
                    net_gain = (price * units) - total_bought_price
                    percent_gain = ((price - bought_price) / bought_price) * 100
                    if percent_gain > 0:
                        risers.append((key, percent_gain, net_gain))
                    else:
                        fallers.append((key, percent_gain, net_gain))
                except:
                    continue
        return risers, fallers

    def review_portfolio(self, account):
        print(datetime.now(), 'review_portfolio')
        for key in account.portfolio.keys():
            print(key, account.portfolio[key])
        value = self.get_value(account)
        print('current stock value:', value)
        print('current cash:', account.funds)
        if type(value) == float:
            print('current total value:', str(value + account.funds))
        actions = {'buy': 0, 'sell': []}
        if float(account.funds) > 250:
            actions['buy'] = 1
        sell_shares = []
        if account.portfolio != {}:
            for key in account.portfolio.keys():
                try:
                    share = account.portfolio[key]
                    bought_price = float(share.price)
                    units = float(share.holding)
                    total_bought_price = bought_price * units
                    s = Share(key)
                    price = float(s.get_price())
                    net_gain = (price * units) - total_bought_price
                    print(key, net_gain)
                    day7_price, _ = self.predict_stock(key)
                    if float(day7_price) <= price * 0.9:
                        sell_shares.append(key)
                        print(key, 'is predicted to fall this week: time to sell')
                    elif net_gain > 500:
                        sell_shares.append(key)
                        print(key, 'has risen significantly: sell and bank the proceeds')
                    elif price > bought_price and price > (float(s.get_50day_moving_avg()) * 1.05) \
                                                      and price > (float(s.get_200day_moving_avg()) * 1.05):
                        sell_shares.append(key)
                        print(key, 'is well above its rolling average: selling')
                except Exception as e:
                    print(e)
                    print("don't know whether to sell")
        
        if len(sell_shares) > 0:
            actions['sell'] = sell_shares
        print("looking to sell")
        for share in sell_shares:
            print(share)
        return actions

    def sell_stocks(self, account, actions):
        print(datetime.now(), 'sell_stocks')
        if actions['sell'] == []: return account, ''
        print(actions)
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
                proceeds = current_price * holding.holding
                total_proceeds += proceeds
                total_cost = holding.holding * holding.price
                profit = proceeds - total_cost
                print("sold", stock, "at", current_price)
                print("profit: ", profit)
                sell_statement.append((stock, profit))
                portfolio.pop(stock, None)
                account.history.append([datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'), 'sold ' \
                                        + str(holding.holding) + ' ' + stock + '(' + str(profit) + ')' \
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

    def update_watchlist(self, account):
        print(datetime.now(), 'update_watchlist')
        all_shares = get_stock_list.get_stocks()[3:]
        for share in all_shares:
            try:
                s = Share(share)
                price = s.get_price()
                if price < s.get_50day_moving_avg() and price < s.get_200day_moving_avg() * 0.975:
                    account.watchlist[share] = price
            except Exception:
                pass

    def generate_buy_list(self, account):
        print(datetime.now(), 'generate_buy_list')
        buy_list = []
        for key in account.watchlist.keys():
            try:    
                s = Share(key)
                price = s.get_price()
                watch_price = account.watchlist[key]
                if price > watch_price and price < s.get_50day_moving_avg() and price < s.get_200day_moving_avg():
                    buy_list.append(key)
            except Exception:
                pass
        return buy_list

    def predictive_buy(self, account):
        print(datetime.now(), 'predictive_buy')
        print("getting latest forecasts...")
        self.get_predictions()
        today = datetime.strftime(datetime.now(), '%Y-%m-%d')
        df = Broker.forecasts.copy()
        df = df[df['date_made'] == today]
        try:
            df['prediction'] = pd.to_numeric(df['prediction'], errors='coerce')
            df = df[df['prediction'] >= (df['base_value'] * 1.15)]
            print("the following stocks are predicted to rise:")
            print(df)
        except Exception as e:
            print(e)
            return self.buy_stocks(account, {'buy': 0}, [])
        account, buy_statement = self.buy_stocks(account, {'buy': 1}, list(df['stock']))
        return account, buy_statement

    def buy_stocks(self, account, actions, buy_list=None):
        print(datetime.now(), 'buy_stocks')
        funds = float(account.funds) / 3
        remaining_funds = float(account.funds) - funds
        if actions['buy'] == 0 or funds < 900: return account, choice(['nothing caught my eye', "i'm skint",
                                                                        "i'm out dogging i'll be trading later"])

        # check watchlist for shares moving up
        if buy_list == None:
            buy_list = self.generate_buy_list(account)
        print("looking to buy", buy_list)
                
        # add shares to watchlist
        self.update_watchlist(account)

        # buy shares
        portfolio = account.portfolio
        if buy_list == []: return account, "i'm too high to buy " + str(choice([';/', '!!', '...?', ':/', ':p']))
        buy_statement = ''
        shuffle(buy_list)
        for stock in buy_list:
            try:
                s = Share(stock)
                current_price = float(s.get_price())
            except Exception:
                print("network error: could not process transaction for", stock)
                return account, 'the market is overvalued'
            num_shares = int((funds / 5) / current_price)
            if num_shares < 1:
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

    def get_predictions(self):
        print("connecting to EC2 instance...")
        try:
            subprocess.call(['scp', '-i', '28nov.pem',
                             'ubuntu@ec2-52-53-234-188.us-west-1.compute.amazonaws.com:predictions.csv', '.'])
            print("connected")
        except Exception as e:
            print(e)
        else:
            print("retrieved latest forecasts")
            with open(forecast_file, 'r') as f:
                forecasts = pd.read_csv(f)
            f.close()
            print(forecasts)
        Broker.forecasts = forecasts

    def make_predictions(self, n=5):
        print(datetime.now(), 'make_predictions')
        df = Broker.forecasts.copy()
        indices = list(df.index)
        indices = sample(indices, min(n, len(indices)))
        stock_tips = []
        for i in indices:
            stock_tips.append(df.iloc[i])
        return stock_tips

    def predict_stock(self, stock):
        print(datetime.now(), 'predict_stock')
        forecasts = Broker.forecasts
        found = 0
        try:
            forecasts = forecasts[forecasts['stock'] == stock]
            price, trigger_date = forecasts[-1:]['prediction'].values[0], forecasts[-1:]['trigger_date'].values[0]
            if float(price) > 0: found = 1
        except Exception as e:
            print(e)
        if found != 1:
            try:
                p = Price_Predictor(stock)
                price = p.predict()
                trigger_date = datetime.strftime(datetime.now() + timedelta(days=7), '%Y-%m-%d')
                self.save_prediction(price, stock)
            except Exception as e:
                print(e)
                return
        trigger_date = datetime.strftime(datetime.strptime(trigger_date, '%Y-%m-%d'), '%d %B')
        price = int(float(price))
        return price, trigger_date

    def get_stock_tips(self):
        today = datetime.strftime(datetime.now(), '%Y-%m-%d')
        df = Broker.forecasts.copy()
        df = df[df['date_made'] == today]
        try:
            df['prediction'] = pd.to_numeric(df['prediction'], errors='coerce')
            df['gain'] = (df['prediction'] - df['base_value']) / df['base_value']
            df['gain'].dropna(inplace=True)
            df.sort_values('gain', ascending=False, inplace=True)
            df.drop_duplicates('stock', inplace=True)
            print(df)
            climbers = df['stock'][0:3]
            fallers = df['stock'][-3:]
            return list(climbers), list(fallers)
        except Exception as e:
            print(e)

    def save_prediction(self, price, stock):
        temp = {}
        try:
            s = Share(share)
            base_value = s.get_price()
        except:
            return
        temp['stock'] = stock
        temp['date_made'] = datetime.strftime(datetime.now(), '%Y-%m-%d')
        temp['trigger_date'] = datetime.strftime(datetime.now() + timedelta(days=7), '%Y-%m-%d')
        temp['base_value'] = base_value
        temp['prediction'] = price
        temp['prediction'] = pd.to_numeric(temp['prediction'], errors='coerce')
        Broker.forecasts = Broker.forecasts.append(temp, ignore_index=True)
        Broker.forecasts = Broker.forecasts[['stock', 'date_made', 'trigger_date', 'base_value',
                                             'prediction', 'actual', 'error']]
        print("prediction saved")
    
    def manage_accounts(self, num=None):
        hours, minutes = [8, 12, 15], [10, 11, 12, 30, 31, 32, 33, 34]
        if datetime.now().hour in hours and datetime.now().minute in minutes:
            # update predictions
            self.get_predictions()
            predictions = [(datetime.strftime(datetime.strptime(p.trigger_date, '%Y-%m-%d'), '%d %B'),
                            p.stock, int(float(p.prediction))) for p in self.make_predictions()]
            print("predictions:")
            for p in predictions:
                print("by {0.trigger_date} {0.stock} will be at around {0.prediction}".format(p))     
        if num == None:
            accounts = self.accounts
            for account in accounts:
                if market_open():
                    comment = self.update_portfolio(accounts[account].num)
                    print(accounts[account].num, accounts[account].name)
                    print(comment)
        else:
            account = self.accounts[num]
            self.accounts[num] = account
            print(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M'))
            if market_open(): print("market open")
            else: print("market closed")
            if True or market_open():
                comment = self.update_portfolio(account.num)
                print(account.num, account.name)
                print(comment)
        self.save_accounts()

    def save_accounts(self):
        accounts = self.accounts
        print("saving")
        with open(data_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(('num', 'name', 'portfolio', 'funds', 'watchlist', 'history'))
            writer.writerows([(accounts[client].num, accounts[client].name, accounts[client].portfolio,
                               accounts[client].funds, accounts[client].watchlist, accounts[client].history)
                               for client in accounts])
        f.close()




if __name__ == '__main__':
    b = Broker()
    while True:
        b.manage_accounts()
        time.sleep(600)
