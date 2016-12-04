from subprocess import check_output
import re
import time
from time import strftime
from twython import Twython, TwythonStreamer
from random import choice
import requests
import json
import stock_broker

#######################################################
## Twitter authentication
#######################################################

APP_KEY = '7OsGVWyMIbHi7cOrliCmDZqyt'
APP_SECRET = 'ZOMMJLKedEZMruEpZYSlF92gYNJzwuWAvxCngY4LjVY21AXwxw'
OAUTH_TOKEN = '800096652438556672-uraCDWbMz7qCPwOdXa9IiVcVtGu1kbn'
OAUTH_SECRET = 'noVWZuxm7yGme6jI2pnXZZNlYSVeTIgyU4izzThJPQZlC'

p = re.compile('\d+.\d*')
p2 = re.compile('the markets')
x = 0

#######################################################
## commentary
#######################################################

comments = ['#ferrari, #shooting, #capri',
            'chateau #petrus, #cuban cigars, #croquet',
            '#chablis, #richmond, #coke',
            "i'm bloody #loaded",
            'i say',
            'goodfellow',
            'frankly i feel sorry for these #plebs',
            '#rollsroyce',
            'give them both barrels Henry!',
            'where is my bloody butler',
            'blowjob on my #yacht',
            "i'm in the front row at #wimbledon where are you?",
            'brevity is the soul of wit',
            'say hi to your mum',
            'get out of my way',
            'if the salary and benefits are appropriate i am available for immediate start #banking #jobs',
            'my therapist says only three of my cores are peverted #porn #ftse #hornybanker',
            'you will cream yourself when you see my portfolio']

words = ['richmond', 'mayfair', 'lords', 'coke', 'drugs', 'nasdaq', 'dowjones', 'ftse', 'bloomberg', 'banker']

def say_comment(twitter, comment=None):
    if comment == None:
        comment = choice(comments)
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

def fave(query, t, count=75):
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
## Discussions
#######################################################

discussions = ['get a job...',
               "you don't really believe that??",
               "when i was starting out in the city i used to believe that too...",
               "we all know gaul was divided into three parts. and now??",
               "i will not be booking gary glitter for any more christmas parties",
               "no...",
               "nobody expects the spanish inquisition either",
               "i had chateau petrus for breakfast... #richkid"]

dqs = ['brexit bremoaner', 'london city finance', 'france election', 'sunderland brexit chav', 'finance economics',
      'immigrants brexit chav']

def discussion(t):
    print("starting discussion")
    q = choice(dqs)
    print(q)
    try:
        tweets = t.search(q=q, count=3)
    except Exception as e:
        tweets = []
        print(e)
    
    if tweets != []:
        for r in tweets['statuses']:
            message = choice(discussions)
            user = r['user']['screen_name']
            id = r['id_str']
            message = '@' + user + ' ' + message
            print(message)
            try:
                t.update_status(status=message, in_reply_to_status_id=id)
                print()
            except Exception as e:
                print(e)

#######################################################
## jobs
#######################################################

messages = ["i'm perfect for this role", "if the package is right, i'll take it. hit me back",
            "i am PASSIONATE about this role. What are the stock options?",
            "if you can go 100k ++ we can talk. hit me back",
            "i can do this job. available for immediate start. hit me back",
            "i am getting a lot of interest. call me quick. 100k ++",
            "the role sounds perfect. let's talk money",
            "im' interested... what's the package?",
            "i am always growing my skill set. i would be a credit to any organisation",
            "my skillset is vast",
            "i have only been fired ONCE and that was a misunderstanding and no charges were ultimately brought",
            "what are the stock options and what is the dress code please? hit me back!"]

qs = ['jobs careers finance', 'finance jobs', 'wall street careers', 'banking careers apply role', 'city jobs finance',
      'finance recruitment jobs london', 'city banking recruitment', 'finance tech jobs roles']

def find_jobs(t):
    print("applying for jobs")
    q = choice(qs)
    print(q)
    try:
        tweets = t.search(q=q, count=3)
    except Exception as e:
        tweets = []
        print(e)
    
    if tweets != []:
        for r in tweets['statuses']:
            message = choice(messages)
            user = r['user']['screen_name']
            id = r['id_str']
            message = '@' + user + ' ' + message
            print(message)
            try:
                t.update_status(status=message, in_reply_to_status_id=id)
                print()
            except Exception as e:
                print(e)

#######################################################
## new follows
#######################################################

topics = ['nasdaq', 'algorithmic', 'bloomberg', 'ftse', 'banking', 'banker', 'london',
          'cityoflondon', 'hooker', 'escorts']

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
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET)
    x = 151
    while True:
        if x % 151 == 0: discussion(twitter)
        if x % 7 == 0: find_jobs(twitter)
        market_action, balances, predictions = stock_broker.get_market_action()
        print(balances)
        for p in predictions[:3]:
                say_comment(twitter, "by {0.trigger_date} {0.stock} will be at {0.prediction}".format(p))
        desc = 'trader, connoisseur, love croquet.' + \
               '                                Cash: ' + str(int(balances[1])) + \
               '      equities: ' + str(int(balances[0])) + \
               '      total: ' + str(int(sum(balances)))
        if x % 3:
            try:
                twitter.update_profile(description=desc)
            except:
                print("could not update balance")
        if choice(range(5)) == 2:
            market_action += ". i'm bloody #loaded"
        print(market_action)
        say_comment(twitter, market_action)
        if re.match(p2, market_action):
            say_comment(twitter, "time for a nightcap " + str(choice(['?', '!', '#tired'])))
            time.sleep(5000)
        if x % 8 == 0: say_comment(twitter)
        if x % 9 == 0: say_cpu(twitter)
        #if x % 25 == 0: make_friends(twitter)
        if x % 15 == 0: purge_follows(twitter)
        if x % 13 == 0:
            word = choice(words)
            print("favourite: ", word)
            fave(word, twitter)
        x += 1
        time.sleep(750)

################

if __name__ == '__main__':
    main_loop()

