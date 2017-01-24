from __future__ import absolute_import, unicode_literals
from .celery import app


@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def xsum(numbers):
    return sum(numbers)

@app.task
def update_predictions(shares):
    import pandas as pd
    from datetime import datetime, timedelta
    from proj.predictor import Predictor
    from yahoo_finance import Share
    from random import sample
    import get_stock_list
    import time
    return 42
