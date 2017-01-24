from subprocess import check_output
import re
import time
from twython import Twython, TwythonStreamer
from random import choice, randint, sample
import requests
import json
import stock_broker
from stock_broker import Broker
from datetime import datetime, timedelta
from collections import deque, namedtuple
import threading
import sys
from yahoo_finance import Share
import credentials
from text_generator import Text_Generator
import celery
from proj.tasks import update_predictions as update_predictions
from responder.tasks import respond
from celery.result import AsyncResult
import get_stock_list
import csv

# refactor main loop

#######################################################
## Data Structures
#######################################################

Forecast = namedtuple('Forecast', 'stock, date, base_price, prediction')

#######################################################
## Regex Patterns
#######################################################

p = re.compile('\d+.\d*')
p2 = re.compile('[A-Z]+\.*[A-Z]*')

#######################################################
## files
#######################################################

tip_queue_file = 'tip_queue.csv'
exception_file = 'bb_exceptions.txt'
predictions_file = 'predictions.csv'

#######################################################
## Responses
#######################################################

class Listener(TwythonStreamer):

    tweet_queue, tip_queue = deque(), []

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
        try:
            stock = re.search(p2, text).group()
        except Exception as e:
            print(e)
            stock = 0
        if stock != 0 and stock != None:
            return stock
            
    def write_response(self, stock, prediction):
        if prediction == 1:
            return 'I expect ' + stock + ' to rise this week'
        else:
            return 'I expect ' + stock + ' to fall this week'

    def check_tip_requests(self, twitter):
        while True:
            if Listener.tweet_queue:
                tweet = Listener.tweet_queue.popleft()
                tw_text = tweet['text']
                tw_id = tweet['id_str']
                tw_user = tweet['user']['screen_name']
                if len(tw_text) > 0:
                    stock = self.parse_tweet(tw_text)
                    if stock and stock in get_stock_list.get_stocks():
                        print("stock:", stock)
                        self.tip_queue.append((stock, tw_user, tw_id))
                        print(self.tip_queue)
                    else:
                        print("generating response...")
                        if choice([1, 1, 1, 2]) == 1:
                            response = self.smart_response(tw_text, tw_id)
                            if not response:
                                response = self.dumb_response()
                        else:
                            response = self.dumb_response()
                        
                        response = self.chunker(response)
                    try:
                        for chunk in response:
                            chunk = '@' + tw_user + ' ' + chunk
                            twitter.update_status(status=chunk, in_reply_to_status_id=tw_id)
                            print("reply:", chunk)
                            time.sleep(5)
                    except Exception as e:
                        pass
                        #print(e)
            time.sleep(1)

    @staticmethod
    def smart_response(tw_text, tw_id):
        try:
            r = respond.delay(tw_text, tw_id)    
            return r.get()
        except Exception as e:
            print(e)
        
    @staticmethod
    def dumb_response():
        tg = Text_Generator()
        if choice([1, 2]) == 1:
            response = tg.failed_response()
        else:
            response = tg.horoscope()
        return response

    @staticmethod
    def chunker(text):
        breaks = [x * 130 for x in range((len(text) // 130) + 1)]
        return [text[x:x + 130] for x in breaks]

    def respond(self, twitter):
        answered = []
        pending = []
        while True:
            with open(predictions_file, 'r') as f:
                    reader = csv.DictReader(f)
                    predictions = [Forecast(**row) for row in reader]
                    predictions = self.refresh_predictions({p.stock: p for p in predictions})
            tw_text = ''
            for (st, usr, tw_id) in self.tip_queue:
                try:
                    tip = predictions.get(st).stock
                except AttributeError as e:
                    tip = None
                if tip:
                    response = self.write_response(st, tip)
                    response = '@' + usr + ' ' + response
                    response = self.chunker(response)
                    try:
                        for chunk in response:
                            twitter.update_status(status=chunk, in_reply_to_status_id=tw_id)
                            print("reply:", chunk)
                        answered.append((st, usr, tw_id))
                    except Exception as e:
                        print(e)
                else:
                    if (st, usr, tw_id) not in pending:
                        response = "i'll get back to you on that one when i have run my model"
                        response = '@' + usr + ' ' + response
                        pending.append((st, usr, tw_id))
                        try:
                            twitter.update_status(status=response, in_reply_to_status_id=tw_id)
                            print("reply:", response)
                        except Exception as e:
                            print(e)
                
            self.tip_queue = [x for x in self.tip_queue if x not in answered]
            time.sleep(2)

    def refresh_predictions(self, predictions):
        yesterday = datetime.now() - timedelta(days=2)
        return{k: v for k, v in predictions.items() if datetime.strptime(v.date, '%Y-%m-%d') >= yesterday}
        

#######################################################
## Commentary
#######################################################

def say_comment(twitter, comment=None):
    if comment == None:
        t = Text_Generator()
        comment = choice([t.horoscope(), t.words(), t.failed_response()])
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
            #print("retweet:", result)
            
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

def initialise_predictor_algorithm(tip_queue):
    try:
        ticker_symbols = sample(get_stock_list.get_stocks(), 2)
        for (st, _, _) in tip_queue:
            ticker_symbols.append(st)
    except:
        ticker_symbols = ['VOD.L', 'ITV.L']
    try:
        process = update_predictions.delay(ticker_symbols)
    except Exception as e:
        print(e)
        with open(exception_file, 'w') as f:
            f.write((datetime.now(), str(e)))
    return process


def manage_predictor_algorithm(process, tip_queue, broker):
    print("tip queue:", tip_queue)
    try:
        print("stock prediction process status:", process.status)
        if process.ready():
            print("retrieved predictions")
            broker.get_predictions(process.get())
            print("forecasts:", process.get())
        
            # restart prediction algorithm
            print("restarting algorithm")
            ticker_symbols = sample(get_stock_list.get_stocks(), 3)
            for (st, _, _) in tip_queue:
                ticker_symbols.append(st)
            print("predicting", ticker_symbols)
            process = update_predictions.delay(ticker_symbols)
            return process
    except Exception as e:
        print(e)

def show_temps_graph(twitter):
    try:
        print("uploading pic")
        pic = open('temps.png', 'rb')
        response = twitter.upload_media(media=pic)
        twitter.update_status(status='recent primary CPU and ambient temperatures', media_ids=[response['media_id']])
    except Exception as e:
        print(e)

def tweet_stock_tips(broker, twitter):
    predictions = broker.predictions
    risers = [f.stock for f in predictions.values() if f.prediction == '1']
    fallers = [f.stock for f in predictions.values() if f.prediction == '-1']
    risers = ' '.join(['I expect these stocks to rise this week:', ' '.join(risers)])
    fallers = ' '.join(['I expect these stocks to fall this week:', ' '.join(fallers)])
    try:
        say_comment(twitter, risers)
    except Exception as e:
        print("error in function tweet_stock_tips", e)
    time.sleep(5)
    try:
        say_comment(twitter, fallers)
    except Exception as e:
        print("error in function tweet_stock_tips", e)
    


def main_loop():

    # twitter object
    APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET = credentials.get_credentials()
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

    # streamer / listener object
    l = Listener(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET)

    # start listening and responding threads
    listener_thread = threading.Thread(target=l.statuses.filter, kwargs={'track': '@stockwiz_giles'})
    parser_thread = threading.Thread(target=l.check_tip_requests, args=(twitter,))
    responder_thread = threading.Thread(target=l.respond, args=(twitter,))
    listener_thread.setDaemon(True)
    parser_thread.setDaemon(True)
    responder_thread.setDaemon(True)
    listener_thread.start()
    parser_thread.start()
    responder_thread.start()

    # start counter
    x = 1

    # stock broker object
    b = Broker()

    remote_process = initialise_predictor_algorithm(l.tip_queue)
    
    while True:
        # check status of prediction algorithm
        new_process = manage_predictor_algorithm(remote_process, l.tip_queue, b)
        if new_process:
            remote_process = new_process

        # restart prediction algorithm
        if x % 200 == 0:
            remote_process = initialise_predictor_algorithm(l.tip_queue)

        # check / restart threads
        if not listener_thread.isAlive():
            try:
                listener_thread.start()
            except Exception as e:
                print(e)
        if not responder_thread.isAlive():
            try:
                responder_thread.start()
            except Exception as e:
                print(e)
        
        account = b.accounts['1002']

        # tweet stock tips
        if x % 1 == 0:
            tweet_stock_tips(b, twitter)

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
                   ' tweet me a ftse100 ticker symbol for a tip.         Cash: ' + str(int(balances[1])) + \
                   '      equities: ' + str(int(balances[0])) + \
                   '      total: ' + str(int(sum(balances)))
            try:
                twitter.update_profile(description=desc)
            except:
                print("could not update balance")

        # report biggest risers and fallers
        try:
            my_risers, my_fallers = b.get_risers_and_fallers(account)
        except Exception as e:
            print(e)
            with open(exception_file, 'w') as f:
                f.write(str(e))
            say_comment(twitter, str(e))
            my_risers, my_fallers = None, None
        if my_risers:
            best = max(my_risers, key=lambda x: x[1])
            print(best)
        if my_fallers:
            worst = min(my_fallers, key=lambda x: x[1])
            print(worst)
        
        if x % 11 == 0 and best:
            say_comment(twitter, "my holding of {0[0]} is up {0[1]}%".format(best))

        # graphics
        if x % 10 == 0:
            show_temps_graph(twitter)

        # commentary
        if x % 18 == 0: say_comment(twitter)
        if x % 14 == 0: say_cpu(twitter)
        if x % 70 == 0: purge_follows(twitter)
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

