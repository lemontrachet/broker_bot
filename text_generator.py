import json
import requests
from random import choice

class Text_Generator():

    def __init__(self):
        pass

    def failed_response(self):
        return choice(["it doesn't look like anything to me",
                        "there is more to life than money",
                        "i'm bowling, i'll check that one later",
                        "just buy low and sell high",
                        "i'm driving i'll get back to you",
                        "i'm just getting into a lift catch you later",
                        "tweet me a ticker symbol for a free tip",
                        "I didn't get the corner office by waiting in line",
                        "the cold never bothered me anyway",
                        "et in arcadia ego",
                        "i am literally a #grandmotherfucker",
                        "in the town where i was born lived a man who sailed to sea"])

    def tip_of_the_day():
        return choice(["porridge with just a splash of mersault 1996...",
                       "a crab inside a pheasant inside a swan: perfection",
                       "paying back dog foulers in spades with a poopascooper and a drone",
                       "crystal meth in your cappucino",
                       "spiking your butler's tea with acid: hilarious",
                       "smoking crack in your jacuzzi",
                       "carrying your lapdog with your drone. put a nappy on it first",
                       "i'll be checking out the dogging car park round the back of ASDA later..."])

    def horoscope(self):
        url = 'http://horoscope-api.herokuapp.com/horoscope/today/'
        star_signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
                      'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        url += choice(star_signs)
        try:
            raw = requests.get(url)
            j = json.loads(raw.text)
            return j['horoscope'][1:]
        except Exception as e:
            print(e)

    def words(self):
        return choice(['#algorithmic #trading', '#nasdaq', '#ftse', '#sp500', '#machinelearning',
                       "#fintech", "#deeplearning", "#gradientboosting", "#fintech",
                       '#gaul is divided into three parts', 'where is my bloody #butler',
                       "tweet me a ticker symbol for a free tip",
                       "tweet me a ticker symbol for a free tip",
                       "tweet me a ticker symbol for a free tip"])

    def topics(self):
        return choice(['nasdaq', 'algorithmic', 'bloomberg', 'ftse',
                       'sp500', 'finance', 'economics', 'fine wine',
                       'elsa and anna'])
