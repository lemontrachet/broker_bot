from concurrent import futures
import pandas as pd
from datetime import datetime, timedelta
from stock_predictor import Price_Predictor
from yahoo_finance import Share
from random import sample
import get_stock_list
import time
import numpy as np

filename = 'predictions.csv'

def predict(share):
    temp = {}
    s = Share(share)
    p = Price_Predictor(share)
    temp['stock'] = share
    temp['date_made'] = datetime.strftime(datetime.now(), '%Y-%m-%d')
    temp['trigger_date'] = datetime.strftime(datetime.now() + timedelta(days=7), '%Y-%m-%d')
    temp['base_value'] = s.get_price()
    temp['prediction'] = p.predict()
    temp['prediction'] = pd.to_numeric(temp['prediction'], errors='coerce')
    #temp['actual'] = np.nan
    #temp['error'] = np.nan
    return temp

def generate_predictions():
    shares = sample(get_stock_list.get_stocks()[3:], 3)
    with futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = executor.map(predict, shares)
    return list(results)

def get_error(actual, prediction):
    if type(actual) == str or type(prediction) == str: return
    if actual == 0 or prediction == 0: return
    return np.abs(actual - prediction) / actual

def evaluate_predictions(df):
    today = datetime.strftime(datetime.now(), '%Y-%m-%d')
    df['actual'] = df[df['trigger_date'] == today]['stock'].apply(get_adj_price)
    df['actual'] = pd.to_numeric(df['actual'], errors='coerce')
    df['error'] = df.apply(lambda row: get_error(row['actual'], row['prediction']), axis=1)
    print(df)
    print("mean error:", df['error'].mean())
    print("median error:", df['error'].median())
        
def get_adj_price(stock):
    today = datetime.strftime(datetime.now(), '%Y-%m-%d')
    yesterday = datetime.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%d')
    try:   
        s = Share(stock)
        return s.get_historical(yesterday, today)[-1]['Adj_Close']
    except:
        return 0 

def load_data():
    try:
        with open(filename, 'r') as f:
            df = pd.read_csv(f)
            f.close()
    except:
        df = pd.DataFrame(columns=['stock', 'date_made', 'trigger_date', 'base_value', 'prediction',
                                   'actual', 'error'])

    df = df[['stock', 'date_made', 'trigger_date', 'base_value', 'prediction']]
    df['prediction'] = pd.to_numeric(df['prediction'], errors='coerce')
    #df = df.dropna()
    return df

def save_data(df):
    print("saving data...")
    with open(filename, 'w') as f:
        df.to_csv(f)
    f.close()
    print("done")

if __name__ == '__main__':
    df = load_data()
    print("checking forecasts")
    evaluate_predictions(df)
    
    while True:
        try:
            results = generate_predictions()
            print("done")
        except Exception as e:
            print("error: stopping")
            print(e)
            results = []
        
        if results != []:
            for r in results:
                df = df.append(r, ignore_index=True)
        df = df[['stock', 'date_made', 'trigger_date', 'base_value', 'prediction', 'actual', 'error']]
        print(df)
        print()
        save_data(df)
        print("sleeping")
        time.sleep(18000)
