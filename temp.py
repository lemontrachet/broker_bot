from subprocess import check_output
import re
import time
from random import choice
from time import strftime
import requests
import json
from matplotlib import pyplot as plt
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
import pandas as pd
from datetime import datetime, timedelta

#######################################################
## weather forecast
#######################################################

def get_weather():
    location = 'Manchester'
    url = ('http://api.wunderground.com/api/acf7c74db5003246/geolookup/conditions/q/UK/'+location+'.json')
    try:
        r = requests.get(url)
        parsed_json = r.json()
        weather_dict = {
            'temp_c' : parsed_json['current_observation']['temp_c'],
            'precip' : parsed_json['current_observation']['precip_today_metric'],
            'pressure' : parsed_json['current_observation']['pressure_mb'],
            'humidity' : parsed_json['current_observation']['relative_humidity'],
            'winddir' : parsed_json['current_observation']['wind_degrees']}
    except Exception: weather_dict = {}
    return weather_dict.get('temp_c')


#######################################################
## CPU
#######################################################

p = re.compile('\d+.\d*')

def say_cpu(temp, ambient):
    ttemp = "CPU at " + temp + " C "
    ambtemp = "ambient: " + str(ambient) + " C "
    print(ttemp, ambtemp)


#######################################################
## Graphics
#######################################################

def make_graph():
    with open("cpu_temp.csv", 'r') as f:
        df = pd.read_csv(f, names=['time', 'temp'])
    with open("ambient_temp.csv", 'r') as f:
        df2 = pd.read_csv(f, names=['time', 'ambient'])
    pd.to_datetime(df['time'])
    pd.to_datetime(df2['time'])
    data_len = min(2000, min(df.shape[0], df2.shape[0]))
    dates, temps = df['time'][:data_len], df['temp'][:data_len]
    ambients = df2['ambient'][:data_len]
    fig, ax = plt.subplots()
    ax.plot_date(dates, temps, '-')
    ax.plot_date(dates, ambients, '-')
    fig.autofmt_xdate()
    #plt.show()
    plt.savefig('temps.png')
    time.sleep(5)
    plt.close()
    


#######################################################
## main
#######################################################    

def main_loop():
    x = 0
    while True:
        temp = check_output(["vcgencmd", "measure_temp"])
        temp = temp.decode("UTF-8")
        temp = re.search(p, temp).group()
        ambient = get_weather()
        if x % 10 == 0: say_cpu(temp, ambient)
        if x % 60 == 0: make_graph()
        with open("cpu_temp.csv", "a") as f:
            temp = float(temp)
            f.write("{0},{1}\n".format(strftime("%Y-%m-%d %H:%M:%S"), str(temp)))
        if ambient:
            with open("ambient_temp.csv", "a") as f:
                ambient = float(ambient)
                f.write("{0},{1}\n".format(strftime("%Y-%m-%d %H:%M:%S"), str(ambient)))
        time.sleep(60)
        x += 1

################

main_loop()

