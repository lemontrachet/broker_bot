from subprocess import check_output
import re
import time
from twython import Twython, TwythonStreamer
from random import choice, randint
import requests
import json
import stock_broker
from stock_broker import Broker
from datetime import datetime, timedelta
from collections import deque
import threading
import sys
from yahoo_finance import Share
import credentials
from text_generator import Text_Generator

### TODO
# only keep one prediction per stock per day


#######################################################
## Regex Patterns
#######################################################

p = re.compile('\d+.\d*')
p2 = re.compile('[A-Z]+\.*[A-Z]*')

#######################################################
## Responses
#######################################################

# todo: retry failed predictions

class Listener(TwythonStreamer):

    tweet_queue = deque()

    def on_success(self, data):
        if 'text' in data:
            self.tweet_queue.append(data)
            try:
                print("tweet received:")
                print(data['text'])
            except:
                pass

    def on_error(self, status_code, data):
        print(status_code)

    def parse_tweet(self, text):
        print(text)
        try:
            stock = re.search(p2, text).group()
        except Exception as e:
            print(e)
            stock = 0
        if stock != 0 and stock != None:
            b = Broker()
            try:
                price, trigger_date = b.predict_stock(stock)
                return (stock, price, trigger_date)
            except Exception as e:
                print(e)
                return

    def write_response(self, stock, price, trigger_date):
        if stock and price and trigger_date:
            try:
                s = Share(stock)
                current = s.get_price()
            except:
                current = None
            if current and float(current) > float(price):
                return 'I expect ' + stock + ' to fall to around ' + str(int(float(price))) + ' by ' + str(trigger_date)
            elif current and float(current) < float(price):
                return 'I expect ' + stock + ' to climb to around ' + str(int(float(price))) + ' by ' + str(trigger_date)
            else: return 'I think ' + stock + ' will be at ' + str(int(float(price))) + ' by ' + str(trigger_date)
        elif choice([1, 2]) == 1:
            tg = Text_Generator()
            return choice([tg.failed_response(), tg.horoscope()])
        
        else:
            try:
                b = Broker()
                b.get_stock_tips()
                tip = b.tip
                return "my tip today: check out {0}".format(tip)
            except Exception as e:
                print(e)

    def respond(self, twitter):
        tw_text = ''
        while True:
            if Listener.tweet_queue:
                tweet = Listener.tweet_queue.popleft()
                tw_text = tweet['text']
                tw_id = tweet['id_str']
                tw_user = tweet['user']['screen_name']
            else:
                time.sleep(30)
                continue
            if len(tw_text) > 0:
                spt = self.parse_tweet(tw_text)
                if spt: response = self.write_response(spt[0], spt[1], spt[2])
                else: response = self.write_response(None, None, None)
                response = '@' + tw_user + ' ' + response
                response = response[:139]
                try:
                    twitter.update_status(status=response, in_reply_to_status_id=tw_id)
                    print("reply:", response)
                except Exception as e:
                    print(e)
            time.sleep(60)


#######################################################
## Commentary
#######################################################

def say_comment(twitter, comment=None):
    if comment == None:
        t = Text_Generator()
        comment = t.horoscope()#t.word()
    try:
        twitter.update_status(status=comment)
        print("tweet:", comment)
    except Exception:
        print("error: could not send tweet")
        pass

def say_cpu(twitter):
    temp = check_output(["vcgencmd", "measure_temp"])
    temp = temp.decode("UTF-8")
    temp = re.search(p, temp).group()
    ttemp = "#CPU at " + temp + " C "
    try:
        twitter.update_status(status=ttemp)
        print("tweet:", ttemp)
    except Exception:
        print("error: could not send tweet")
        pass


#######################################################
## retweets
#######################################################

def fave(query, t, count=10):
    try: tweets = t.search(q=query, count=count)
    except Exception: pass
    try:
        for tweet in tweets['statuses']:
            time.sleep(randint(0, 4))
            result = t.create_favorite(id=tweet['id'])
            time.sleep(randint(0, 4))
            result = t.retweet(id=tweet['id'])
            print("retweet:", result)
            
    except Exception:
        print("error: could not retweet")
        pass



#######################################################
## new follows
#######################################################

def make_friends(t):
    t = Text_Generator()
    topic = t.topic()
    try:
        results = t.cursor(t.search, q=topic, count=20)
    except Exception:
        results = []

    if results != []:
        for r in results:
            user = r['user']['screen_name']
            try:
                t.create_friendship(id=user)
                print('followed', user)
                time.sleep(randint(0, 4))
            except Exception:
                pass

def purge_follows(t):
    print("purging")
    try:
        followers = t.get_followers_ids()
        i_follow = t.get_friends_ids()
    except:
        return
    deleted = 0
    new = 0
    try:
        for id in i_follow['ids']:
            if id not in followers['ids']:
                t.destroy_friendship(user_id=id)
                time.sleep(randint(0, 4))
                deleted += 1
        for id in followers['ids']:
            if id not in i_follow['ids']:
                time.sleep(randint(0, 4))
                t.create_friendship(user_id=id)
                new += 1
    except:
        return
    comment = 'unfollowed ' + str(deleted) + ' and followed ' + str(new)
    print(comment)
    say_comment(t, comment)


#######################################################
## main
#######################################################    

def main_loop():
    
    # twitter object
    APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET = credentials.get_credentials()
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

    # streamer / listener object
    l = Listener(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

    # start listening and responding threads
    listener_thread = threading.Thread(target=l.statuses.filter, kwargs={'track': '@stockwiz_giles'})
    responder_thread = threading.Thread(target=l.respond, args=(twitter,))
    listener_thread.start()
    responder_thread.start()
    
    # start counter
    x = 18

    # stock broker object
    b = Broker()
    
    while True:
        account = b.accounts['1002']

        # buy and sell and report actions
        if x % 7 == 0:
            buy_comment, sell_comment = b.update_portfolio('1002')
            b.save_accounts()
            print(buy_comment)
            print(sell_comment)
            say_comment(twitter, buy_comment)
            say_comment(twitter, sell_comment)

        # get account balance and update profile message
        balances = [b.get_value(account), account.funds]
        if type(balances[0]) == str: balances[0] = 0
        if x % 5 == 0 and type(balances[0]) != str and balances[0] > 0:
            desc = 'trader, connoisseur.' + \
                   ' tweet me a ticker symbol for a tip.                 Cash: ' + str(int(balances[1])) + \
                   '      equities: ' + str(int(balances[0])) + \
                   '      total: ' + str(int(sum(balances)))
            try:
                twitter.update_profile(description=desc)
            except:
                print("could not update balance")

        # report biggest risers and fallers
        risers, fallers = b.get_risers_and_fallers(account)
        if risers:
            best = max(risers, key=lambda x: x[1])
            print(best)
        if fallers:
            worst = min(fallers, key=lambda x: x[1])
            print(worst)
        
        if x % 11 == 0 and best:
            say_comment(twitter, "my holding of {0[0]} is up {0[1]}%".format(best))
        
        # stock predictions
        if x % 14 == 0:
            predictions = b.make_predictions()
            for p in predictions[:2]:
                say_comment(twitter, "by {0.trigger_date} {0.stock} will be at about {0.prediction}".format(p))

        # tips
        if x % 28 == 0:
            climbers, fallers = b.get_stock_tips()
            if climbers:
                try:
                    i = 1
                    say_comment(twitter, "my buying tips for today:")
                    for climber in climbers:
                        say_comment(twitter, "{0}/{1} BUY {2}".format(i, len(climbers), climber))
                        time.sleep(10)
                        i += 1
                except Exception as e:
                    print(e)
            if fallers:
                try:
                    i = 1
                    say_comment(twitter, "my selling tips for today:")
                    for faller in fallers:
                        say_comment(twitter, "{0}/{1} SELL {2}".format(i, len(fallers), faller))
                        time.sleep(10)
                        i += 1
                except Exception as e:
                    print(e)
                    
        # commentary
        if x % 18 == 0: say_comment(twitter)
        if x % 14 == 0: say_cpu(twitter)
        if x % 100 == 0: purge_follows(twitter)
        if x % 16 == 0:
            print("retweet")
            t = Text_Generator()
            word = t.topics()
            print("favourite: ", word)
            fave(word, twitter)
            
        print("sleeping until", datetime.strftime(datetime.now() + timedelta(seconds=360), '%T'))
        print("x:", x)
        time.sleep(360)
        x += 1

################

if __name__ == '__main__':
    main_loop()

