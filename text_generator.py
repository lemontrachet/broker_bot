import json
import requests
from random import choice

class Text_Generator():

    def __init__(self):
        pass

    def failed_response(self):
        return choice(["it doesn't look like anything to me",
                        "not sure about that one.",
                        "there is more to life than money",
                        "i'm bowling, i'll check that one later",
                        "just buy low and sell high",
                        "i'm driving i'll get back to you",
                        "i'm just getting into a lift catch you later",
                        "if the stock options are good i will seriously consider the position (100k++)",
                        "exactly",
                        "never even heard of it, i stick to the major exchanges",
                        "tweet me a ticker symbol for a free tip",
                        "i'm not a bot. #microdosing helped me get to the top of my profession",
                        "you wouldn't believe how rich i am"])

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

