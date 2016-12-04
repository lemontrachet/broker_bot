from subprocess import check_output
import re
import time
from twython import Twython, TwythonStreamer
from random import choice
import requests
import json
import stock_broker
from stock_broker import Broker
from datetime import datetime, timedelta
from collections import deque
import threading
import sys
from yahoo_finance import Share

#######################################################
## Twitter authentication
#######################################################

APP_KEY = 'o6uqr48RtXi2rbG6Op4GpTaEW'
APP_SECRET = 'glpOxJuOwfbUeJ2p0372S5PKNbKXwGu1xue45ZCjSnHCCAQxsd'
OAUTH_TOKEN = '804783738089570308-yb82pnsQD8hD9hcYhtKOL7yCkLXU2Ar'
OAUTH_SECRET = 'eRklm3sqRoI6zXnGtFXhNuXv8Fha9iSi6t6zQZSJjiR9r'

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
            print("tweet received:")
            print(data['text'])

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
        failed_responses = ("it doesn't look like anything to me",
                            "not sure about that one.",
                            "there is more to life than money",
                            "i'm out dogging, i'll check that one later",
                            "just buy low and sell high",
                            "i'm too stoned right now believe me you don't want my advice")
        if stock and price and trigger_date:
            try:
                s = Share(stock)
                current = s.get_price()
            except:
                current = None
                pass
            if current and float(current) > float(price):
                return 'I expect ' + stock + ' to fall to around ' + str(int(float(price))) + ' by ' + str(trigger_date)
            elif current and float(current) < float(price):
                return 'I expect ' + stock + ' to climb to around ' + str(int(float(price))) + ' by ' + str(trigger_date)
            else: return 'I think ' + stock + ' will be at ' + str(int(float(price))) + ' by ' + str(trigger_date)
        else:
            return choice(failed_responses)

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
                try:
                    twitter.update_status(status=response, in_reply_to_status_id=tw_id)
                except Exception as e:
                    print(e)
            time.sleep(60)


#######################################################
## Commentary
#######################################################

words = ['#algorithmic #trading', '#nasdaq', '#ftse', '#sp500', '#machinelearning', '#dogging',
         "christmas", "cityoflondon", "deeplearning", "gradientboosting"]

def say_comment(twitter, comment=None):
    if comment == None:
        comment = choice(words)
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
    ttemp = "CPU at " + temp + " C "
    try:
        twitter.update_status(status=ttemp)
        print("tweet:", ttemp)
    except Exception:
        print("error: could not send tweet")
        pass


#######################################################
## retweets
#######################################################

def fave(query, t, count=25):
    try: tweets = t.search(q=query, count=count)
    except Exception: pass
    try:
        for tweet in tweets['statuses']:
            result = t.create_favorite(id=tweet['id'])
            result = t.retweet(id=tweet['id'])
            print("retweet:", result)
            
    except Exception:
        print("error: could not retweet")
        pass



#######################################################
## new follows
#######################################################

topics = ['nasdaq', 'algorithmic', 'bloomberg', 'ftse', 'banking', 'banker', 'london',
          'cityoflondon', 'sp500', 'finance', 'economics']

def make_friends(t):
    topic = choice(topics)
    try:
        results = t.cursor(t.search, q=topic, count=25)
    except Exception:
        results = []

    if results != []:
        for r in results:
            user = r['user']['screen_name']
            try:
                t.create_friendship(id=user)
            except Exception:
                pass

def purge_follows(t):
    print("purging")
    try:
        followers = t.get_followers_ids()
        i_follow = t.get_friends_ids()
    except:
        pass
    deleted = 0
    new = 0
    try:
        for id in i_follow['ids']:
            if id not in followers['ids']:
                t.destroy_friendship(user_id=id)
                deleted += 1
        for id in followers['ids']:
            if id not in i_follow['ids']:
                t.create_friendship(user_id=id)
                new += 1
    except:
        pass
    comment = 'unfollowed ' + str(deleted) + ' and followed ' + str(new)
    print(comment)
    say_comment(t, comment)


#######################################################
## main
#######################################################    

def main_loop():
    
    # twitter object
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

    # streamer / listener object
    l = Listener(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

    # start listening and responding threads
    listener_thread = threading.Thread(target=l.statuses.filter, kwargs={'track': '@stockwiz_giles'})
    responder_thread = threading.Thread(target=l.respond, args=(twitter,))
    listener_thread.start()
    responder_thread.start()
    
    # start counter
    x = 14
    #make_friends(twitter)
    while True:
        comment, balances, predictions = stock_broker.get_market_action()
        if x % 14 == 0:
            for p in predictions[:2]:
                
                say_comment(twitter, "by {0.trigger_date} {0.stock} will be at about {0.prediction}".format(p))
        desc = 'trader, connoisseur.' + \
               ' tweet me a ticker symbol for a tip.                 Cash: ' + str(int(balances[1])) + \
               '      equities: ' + str(int(balances[0])) + \
               '      total: ' + str(int(sum(balances)))
        if x % 9 == 0:
            try:
                twitter.update_profile(description=desc)
            except:
                print("could not update balance")
        print(comment)
        say_comment(twitter, comment)
        if x % 18 == 0: say_comment(twitter)
        if x % 39 == 0: say_cpu(twitter)
        if x % 150 == 0: purge_follows(twitter)
        if x % 16 == 0:
            print("retweet")
            word = choice(words)
            print("favourite: ", word)
            fave(word, twitter)
        x += 1
        print("sleeping until", datetime.strftime(datetime.now() + timedelta(seconds=360), '%T'))
        time.sleep(360)

################

if __name__ == '__main__':
    main_loop()

