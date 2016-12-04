from datetime import *

base_date = datetime.now()
business_start = datetime.strptime(datetime.strftime(base_date, '%Y-%m-%d') + ', 08:00:00', '%Y-%m-%d, %H:%M:%S')
business_end = datetime.strptime(datetime.strftime(base_date, '%Y-%m-%d') + ', 16:30:00', '%Y-%m-%d, %H:%M:%S')
holidays = ['2017-01-02', '2016-12-27', '2016-12-26', '2017-04-14', '2017-04-16', '2017-04-17', '2017-05-01',
                '2017-05-01', '2017-05-29', '2017-08-28', '2017-12-25', '2017-12-26']

def market_open():
    t = datetime.now()
    if t.weekday() > 4:
        return False
    day_only = datetime.strftime(t, '%Y-%m-%d')
    if day_only in holidays:
        return False
    if t < business_start or t > business_end:
        return False
    return True

def time_until_open():
    now = datetime.now()
    day = now.weekday()
    hour = now.hour
    minute = now.minute
    day_delta = 0
    #if day < 5:
    if hour < 9 and minute < 30:
        hour_delta = 8 - hour
    else:
        hour_delta = 8 + 24 - hour

    if minute < 30:
        minute_delta = 30 - minute
    else:
        minute_delta = minute - 30
    
    if day > 4:
        day_delta = 6 - day
   
    return datetime.now() + timedelta(days=0, hours=hour_delta, minutes=minute_delta)



if __name__ =='__main__':
    print(market_open(datetime.now()))

