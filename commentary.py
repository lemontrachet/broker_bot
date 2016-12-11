from bs4 import BeautifulSoup
import requests
from random import choice
import time
from twython import TwythonStreamer
import credentials
import threading

urls = ['https://fr.wikipedia.org/wiki/Wikip%C3%A9dia:Accueil_principal', 'https://en.wikipedia.org/wiki/Main_Page']
urls2 = ['https://en.wikiquote.org/wiki/Main_Page']

def get_commentary():
    raw = requests.get(choice(urls))
    soup = BeautifulSoup(raw.text, 'lxml')
    q = soup.find_all('p')[0].text
    return q[:140]


class quote_grabber(TwythonStreamer):

    commentary = []

    def on_success(self, data):
        if 'text' in data:
            try:
                tweet = data['text']
                print("tweet added to commentary database:")
                #print(tweet)
                quote_grabber.commentary.append(tweet)
            except Exception as e:
                print(e)

    def on_error(self, status_code, data):
        print(status_code)

    def make_tweet(self):
        rep = ['marcus', 'tulius', 'tullius' 'cicero', 'quote', 'quotes', 'famous', 'best', '"', '-', 'rt', '@',
               'http', 'https', '://', 'twitter', '#', '.co', '.com', 'update', 'video', 'tweet', '|']
        while True:
            if quote_grabber.commentary:
                try:
                    tweet = quote_grabber.commentary.pop()
                    tweet = tweet.lower()
                    tweet = ' '.join(filter(lambda x: x[0] != 'st' \
                                            and x[0] != '@', tweet.split()))
                    tweet = ' '.join([x for x in tweet.split() if not x.startswith('st/')])
                    for r in rep:
                        tweet = tweet.replace(r, '')
                    print(tweet)
                except Exception as e:
                    print(e)

if __name__ == '__main__':
    
    a, b, c, d = credentials.get_credentials()
    l = quote_grabber(a, b, c, d)
    qthread1 = threading.Thread(target=l.statuses.filter, kwargs={'track': 'robespierre'})
    qthread2 = threading.Thread(target=l.make_tweet)
    qthread1.start()
    qthread2.start()
    

