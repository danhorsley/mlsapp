from mlsapp.models import Offers, static, WSInfo
from mlsapp.utils import toISBN10, date_to_sql, null_to_blank, find_dims, find_sleep_time
from datetime import date, time
from decouple import config
import pandas as pd
import requests
import ast

def offpop():
    #pops offers model
    #TODO add a is_live logic checker
    #TODO get  read_excel path from WSInfo
    #TODO fix logic on counter of sleep time
    WSI_query = WSInfo.objects.all()
    for ws in len(range(WSI_query)):
        df = pd.read_excel(f'mls/offer_csvs/{ws.wholesaler}.xlsx')
        df.columns= ast.literal_eval(ws.csv)
    isbn_list = [str(x) for x in list(set(list(df['ISBN'])))]
    api_url = "https://api.keepa.com/"
    my_date = date_to_sql(date.today())
    isbns_to_add=[]
    existing_isbns = [x[0] for x in Offers.objects.all().values_list('book_id')]
    
    is_live(isbn_list, existing_isbns) #updates status of is_live in Offers
    
    for isbn in isbn_list: #checks for new names to send request to keepa
        if isbn not in existing_isbns and isbn[:3]=='978':
            isbns_to_add.append(isbn)
            
    num_isbns_to_add = len(isbns_to_add)
    print('number of names to add is ', num_isbns_to_add)
    for isbn in isbns_to_add:
        
        try:
            my_asin = toISBN10(isbn)
            print(isbn, my_asin, f' {num_isbns_to_add} remaining')
            my_book_id = check_or_create_static(isbn)

            req = requests.get(api_url + f"product?key={config('k_api_key')}&domain=2&asin={my_asin}&buybox=1&offers=20")
            sleep_time = find_sleep_time(req)
            _ = Offers(book= my_book_id, jf = req.json()['products'][0], date = my_date)
            _.save()
            time.sleep(sleep_time)
        except:
            print(f"could not add {isbn}")
            pass
        num_isbns_to_add -= 1
        
def is_live(isbn_list, existing_isbns, ws):
    #isbn_list is current offers from wsgi
    #existing_isbns is list of isbns already in offers
    #this function is to make very sure that is_live bool is correct at time of latest offer
    for isbn in existing_isbns:  #change to inactive anything not in current offers
        if isbn not in isbn_list:
            temp_query = Offers.objects.filter(book_id = isbn, wholsaler = ws.wholesaler)
            temp_query.is_live = 0
            temp_query.save()
    for isbn in isbn_list: #change to active anything that has come back into stock (rare but happens)
        if isbn in existing_isbns:
            temp_query = Offers.objects.filter(book_id = isbn, wholsaler = ws.wholesaler)
            temp_query.is_live = 0
            temp_query.save()
            
def check_or_create_static(isbn):
    #checks if isbn already in static, if not it creates it
    #returns the foreign key from static to link to later
    try:
        my_book_id = static.objects.filter(isbn13=isbn)[0]
    except:
        dims = find_dims(isbn)
        dims = [null_to_blank(dims[i],i) for i in range(len(dims))]
        s = static(isbn13 = isbn, title = dims[0][:200],
                    pubdate = date_to_sql(dims[1]),
                    author = dims[2], pubber = dims[3], cover = dims[4],
                    height = dims[5], width = dims[6], thick = dims[7], weight = dims[8], rrp = 0)
        s.save()
        #st = static.objects.filter(isbn13=isbn)[0]
        my_book_id = static.objects.filter(isbn13=isbn)[0]
        
    return my_book_id
            
    
    