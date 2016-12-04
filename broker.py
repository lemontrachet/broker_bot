#!/usr/bin/python3

from stock_broker import Broker
import time

b = Broker()
num = input("enter account no. or 'a' for all: ")
if num == 'a': num = None

while True:
    if num: b.check_balance(num)
    time.sleep(5)
    b.manage_accounts(num=num)
    time.sleep(2000)
