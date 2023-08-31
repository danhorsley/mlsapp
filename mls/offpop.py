from mlsapp.models import Offers, static, WSInfo
from mlsapp.utils import toISBN10, date_to_sql, null_to_blank, find_dims, find_sleep_time, get_google_description
from datetime import date, time, datetime
from django.utils import timezone
import numpy as np
import json
import calendar
from decouple import config
import pandas as pd
import requests
import time
import subprocess #used for pinging a reliable server to check internet
import pytz

def offpop(a_wholesaler):
    #pops offers model for a_wholesaler given as text
    WSI_query = WSInfo.objects.filter(wholesaler = a_wholesaler)
    for ws in WSI_query:
        df = pd.read_excel(f'mls/offer_csvs/{ws.wholesaler}.xlsx')
        #df.columns= ast.literal_eval(ws.csv)
    isbn_list = [str(x) for x in list(set(list(df['ISBN'])))]
    
    d = date.today()
    #my_date = date_to_sql(date.today())
    isbns_to_add=[]
    existing_isbns = [x[0] for x in Offers.objects.filter(wholesaler = WSI_query[0].wholesaler).values_list('book_id')]
    
    is_live(isbn_list, existing_isbns, WSI_query[0]) #updates status of is_live in Offers
    
    for isbn in isbn_list: #checks for new names to send request to keepa
        if isbn not in existing_isbns and isbn[:3]=='978':
            isbns_to_add.append(isbn)
            
    num_isbns_to_add = len(isbns_to_add)
    print('number of names to add is ', num_isbns_to_add)
    for isbn in isbns_to_add:
        
        try:
            my_asin = toISBN10(isbn)
            print(isbn, my_asin)
            while not is_internet_available():
                wait_for_internet()
            my_book_id = check_or_create_static(isbn)  
            req = req_to_keepa(my_asin) #get info from keepa
            sleep_time = find_sleep_time(req, num_isbns_to_add) 
            _ = Offers(book = my_book_id, jf = req.json()['products'][0], date = timezone.datetime(d.year, d.month, d.day, tzinfo=pytz.UTC),
                       wholesaler = WSInfo.objects.filter(wholesaler=ws.wholesaler)[0], is_live=True)
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
    if len(Offers.objects.filter(wholesaler = ws.wholesaler))>0: #check ws has seen previous entries
        for isbn in existing_isbns:  #change to inactive anything not in current offers
            if isbn not in isbn_list and len(Offers.objects.filter(book_id = isbn, wholesaler = ws.wholesaler))>0 :
                temp_query = Offers.objects.filter(book_id = isbn, wholesaler = ws.wholesaler)[0]
                temp_query.is_live = 0
                temp_query.save()
        for isbn in isbn_list: #change to active anything that has come back into stock (rare but happens)
            if isbn in existing_isbns:
                #print(isbn, ws, ws.wholesaler)
                temp_query = Offers.objects.filter(book_id = isbn, wholesaler = ws.wholesaler)[0]
                temp_query.is_live = 1
                temp_query.save()
            
def check_or_create_static(isbn):
    #checks if isbn already in static, if not it creates it
    #returns the foreign key from static to link to later
    try:
        my_book_id = static.objects.filter(isbn13=isbn)[0]
    except:
        dims = find_dims(isbn)
        dims = [null_to_blank(dims[i],i) for i in range(len(dims))]
        
        try:
            c,d = get_google_description(isbn)
        except:
            c = d = ''
        
        s = static(isbn13 = isbn, title = dims[0][:200],
                    pubdate = date_to_sql(dims[1]),
                    author = dims[2], pubber = dims[3], cover = dims[4],
                    height = dims[5], width = dims[6], thick = dims[7], weight = dims[8], rrp = 0,
                    category = c, description= d )
        s.save()
        #st = static.objects.filter(isbn13=isbn)[0]
        my_book_id = static.objects.filter(isbn13=isbn)[0]
        
    return my_book_id

def req_to_keepa(my_asin):
    #returns request from keepa - possibility to increase range of options later
    return requests.get(config('k_url') + f"product?key={config('k_api_key')}&domain=2&asin={my_asin}&buybox=1&offers=20")
            

def is_internet_available():
    hostname = "8.8.8.8"  # Use a reliable external server - google dns 4
    response = subprocess.call(["ping", "-c", "1", hostname], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return response == 0

def wait_for_internet():
    while not is_internet_available():
        print("Internet connection is not available. Waiting...")
        time.sleep(30)  # Adjust the delay as per your requirements
    

def update_hr(ws = 'bestsellers' , cutoff=300000, my_today = date.today()):
    #function updates best ranks in kpop model
    
    my_date = date_to_sql(date.today())
    query = Offers.objects.filter(wholesaler = WSInfo.objects.filter(wholesaler=ws)[0])
    isbns_to_update=[]
    isbnsdf = pd.read_excel('mls/offer_csvs/' + ws + '.xlsx')
    the_isbns = [str(x) for x in list(set(list(isbnsdf['ISBN'])))]
    #find last rank of each name and create list of isbns
    for q in query:
        try:
            #k_data = json.loads(q.jf)
            k_data = q.jf
            temp_rank = avgmaker(k_data['csv'][3])[-1][1]
            temp_date = q.date.date()
            if temp_rank <= cutoff and temp_date < my_today and q.book_id in the_isbns: #isbns66: #isbnsboon:# and q.book_id in 
                isbns_to_update.append(q.book_id)
        except:
            pass
    print(f'number of isbns to update is {len(isbns_to_update)}')
    api_url = "https://api.keepa.com/"
    isbns_left=len(isbns_to_update)
    for my_isbn in isbns_to_update:
        isbns_left -= 1
        my_asin = toISBN10(my_isbn)
        print(f'updating {my_isbn} with asin {my_asin}')
        temp_q = Offers.objects.filter(book_id=my_isbn)[0]
        while not is_internet_available():
                wait_for_internet()
        try:        
            req = requests.get(api_url + f"product?key={config('k_api_key')}&domain=2&asin={my_asin}&buybox=1&offers=20")
            sleep_time = find_sleep_time(req,isbns_left)
            temp_q.jf = req.json()['products'][0]
            temp_q.date = my_date
            temp_q.save()
            time.sleep(sleep_time)
        except:
            print(f"could not add {my_asin}")
        
def avgmaker(my_list,depth=2, ignore_min1=True, ffill=False, nanfill=True, as_list=True, drop_count=True):
    #all objects stored under last day of the month - equal weight given to each data point
    monthly_averages = {}
    my_date = [KTime(x) for x in my_list[0::depth]]
    my_data = my_list[1::depth]
    for item in zip(my_date, my_data):
        if item[1] in [-1,-2] and ignore_min1:
            pass
        else:
            last_day = calendar.monthrange(item[0].year, item[0].month)[1]
            prior_data = monthly_averages.get(date(item[0].year, item[0].month, last_day))
            if prior_data:
                prior_avg, count = prior_data
                new_avg = (prior_avg * count + float(item[1])) / (count + 1) 
                monthly_averages[date(item[0].year, item[0].month, last_day)] = (new_avg, count + 1)
            else:
                monthly_averages[date(item[0].year, item[0].month, last_day)] = (item[1], 1) 
    if drop_count:
        #removes counting used for averages
        for item in monthly_averages:
            monthly_averages[item] = monthly_averages[item][0]
    if ffill:
        if len(monthly_averages)>0:
            monthly_averages = fill_blanks(monthly_averages)
    if nanfill:
        if len(monthly_averages)>0:
            monthly_averages = nan_fill_blanks(monthly_averages)
    if as_list:
        monthly_averages = dict_to_list(monthly_averages)

    return monthly_averages

def fill_blanks(my_dict):
    #take dictionary of dates and averages and forward fill missing month ends
    max_date = max(my_dict.keys())
    min_date = min(my_dict.keys())
    month_ends = [y.date() for y in pd.date_range(min_date,max_date, freq='M').tolist()]
    for i in range(len(month_ends)):
        if my_dict.get(month_ends[i]):
            pass
        else:
            my_dict[month_ends[i]] = my_dict[month_ends[i-1]]
    return my_dict

def nan_fill_blanks(my_dict):
    #take dictionary of dates and averages and forward fill missing month ends
    max_date = max(my_dict.keys())
    min_date = min(my_dict.keys())
    month_ends = [y.date() for y in pd.date_range(min_date,max_date, freq='M').tolist()]
    for i in range(len(month_ends)):
        if my_dict.get(month_ends[i]):
            pass
        else:
            my_dict[month_ends[i]] = np.nan
    return my_dict

def dict_to_list(my_dict):
    return sorted([(j,my_dict[j]) for j in my_dict], key=lambda x: x[0])

def KTime(my_ktime):
    _ = (int(my_ktime) + 21564000)*60
    return datetime.utcfromtimestamp(_)