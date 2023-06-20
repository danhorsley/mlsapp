from ast import excepthandler
from mlsapp.models import KeepaJSONoffers, KeepaMAVG, InvoiceData, static
from decouple import config
import requests
from datetime import date, datetime, timedelta
from collections import Counter
import calendar
import time
import numpy as np
import pandas as pd
from mlsapp.utils import null_to_blank, date_to_sql, toISBN10

def find_sleep_time(my_req,amt_left=0):
    #adjust sleep time to take account of remaining tokens
    tokens_left = my_req.json()['tokensLeft']
    sleep_time = 181
    if int(tokens_left) >= 50 : sleep_time = 120 
    if int(tokens_left) >= 100 : sleep_time = 30
    if int(tokens_left) >= 200 : sleep_time = 10
    if int(tokens_left) >= 1000 : sleep_time = 1
    print(f'you have {tokens_left} tokens left and sleep time is {sleep_time} and {amt_left} isbns remain')
    return sleep_time

def kpopoffers():
    #take list of unique items from InvoiceData
    #request product from keep and store in json format in model
    inv_isbns = list(set([x[0] for x in InvoiceData.objects.all().values_list('book_id')]))
    existing_keepa = list(set([x[0] for x in KeepaJSONoffers.objects.all().values_list('book_id')]))
    api_url = "https://api.keepa.com/"
    my_date = date_to_sql(date.today())
    isbns_to_add = []
    for isb in inv_isbns:
        if isb not in existing_keepa and isb[:3]=='978':
            isbns_to_add.append(isb)
    print('number of names to add is ', len(isbns_to_add))
    for isbn in isbns_to_add:
        my_asin = toISBN10(isbn)
        print(isbn, my_asin)
        req = requests.get(api_url + f"product?key={config('k_api_key')}&domain=2&asin={my_asin}&buybox=1&offers=20")
        sleep_time = find_sleep_time(req)
        try:
            _ = KeepaJSONoffers(book= static.objects.filter(isbn13=isbn)[0], jf = req.json()['products'][0], date = my_date)
            _.save()
        except:
            print(f'could not add {isbn}')
            pass
        time.sleep(sleep_time)