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
                        "i am literally a #grandmotherfucker"])

    def horoscope(self):
        url = 'http://horoscope-api.herokuapp.com/horoscope/today/'
        star_signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
                      'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        url += choice(star_signs)
        try:
            raw = requests.get(url)
            j = json.loads(raw.text)
            return j['horoscope'][1:138]
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
