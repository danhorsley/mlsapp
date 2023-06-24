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
            
    counter = len(isbns_to_add)
    print('number of names to add is ', len(counter))
    
    for isbn in isbns_to_add:
        my_asin = toISBN10(isbn)
        print(isbn, my_asin)
        req = requests.get(api_url + f"product?key={config('k_api_key')}&domain=2&asin={my_asin}&buybox=1&offers=20")
        counter -=1
        sleep_time = find_sleep_time(req, counter)
        try:
            _ = KeepaJSONoffers(book= static.objects.filter(isbn13=isbn)[0], jf = req.json()['products'][0], date = my_date)
            _.save()
        except:
            print(f'could not add {isbn}')
            pass
        time.sleep(sleep_time)
        
def KMAVG_df(my_isbn):
    #takes json from KeepaJSON for 1 isbn and turns it into month end avg model
    print(my_isbn)
    idat = KeepaJSONoffers.objects.filter(book_id=my_isbn)[0].jf
    amzn_px = idat['csv'][0]
    new_px = idat['csv'][1]
    sr = idat['csv'][3]
    print('**sr', sr)
    offers = idat['csv'][11]
    newfba = idat['csv'][10]
    newfbm = squash(idat['csv'][7])
    print(newfba)
    bbx = idat['buyBoxSellerIdHistory']
    bbx = [xx for xx in zip([KTime(x) for x in bbx[0::2]],bbx[1::2])]
    #rat = idat['csv'][16]
    #we need to extract csv[0] - amzn px, csv[1] - new px, csv[3] sales rank, csv[11] - count new, 
    #csv[16] rating, products[0]['buyBoxSellerIdHistory'], csv[18] new buy box plus postage
    if sr is None or len(sr)<=2:
        return pd.DataFrame()
    else:
        cols = [new_px, offers, amzn_px, newfba,newfbm]
        for j in range(len(cols)):
           print(cols[j],'**',['new_px', 'offers', 'amzn_px', 'newfba','newfbm'][j])
           if cols[j] is None:
               cols[j] = [0 if i%2 else x for i,x in enumerate(sr)]
               print(cols[j],'**')
    formatted_lists = [avgmaker(x,as_list=False) for x in [sr] + cols]
    df = pd.DataFrame.from_dict(formatted_lists[0],orient='index')
    for i in range(1,len(formatted_lists)):
        df[i] = df.index.map(formatted_lists[i])
    #print(df)
    #try:
    df.columns = ['sr','new_px', 'offers', 'amzn_px', 'newfba', 'newfbm']
    #except:
    df['sr'] = df['sr'].interpolate()
    df['offers'] = df['offers'].interpolate()
    df['bbx30'] = [bbx_pct(bbx,x,30) for x in df.index]
    df['bbx90'] = [bbx_pct(bbx,x,90) for x in df.index]
    df['bbx30'] = df['bbx30'].interpolate()
    df['bbx90'] = df['bbx90'].interpolate()
    df = df.fillna(0)
    return df

def KMAVG_pop(how = 'new'):
    #set how to 'new or all'
    content = [x[0] for x in KeepaJSONoffers.objects.all().values_list('book_id')]
    existing = [y[0] for y in KeepaMAVG.objects.all().values_list('book_id')]
    iterator = []
    if how == 'new':
        for i in content:
            if i not in existing:
                iterator.append(i)
    else:
        iterator = content
    for c in iterator:
        try:
            df = KMAVG_df(c)
            for i in df.index:
                my_book = static.objects.filter(isbn13=c)[0]
                item = KeepaMAVG(book = my_book, date = date_to_sql(i), new = df['new_px'][i],
                        salesrank = df['sr'][i], offerct = df['offers'][i], AZBBpct30 = df['bbx30'][i],
                        AZBBpct90 = df['bbx90'][i], AZpx = df['amzn_px'][i], newfba = df['newfba'][i],
                        newfbm = df['newfbm'][i])
                item.save()
        except:
            print("could not add last isbn printed")
        

def squash(my_list):
        if my_list:
            x = [my_list[i::3] for i in [0,1,2]]
            y = [z+zz for z,zz in zip(x[1],x[2])]
            nfba = [None]*int(2*len(my_list)/3)
            nfba[::2] = x[0]
            nfba[1::2] = y 
            return nfba
        else:
            return None
        
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

def KTime(my_ktime):
    #turns Keepa time into real time
    _ = (int(my_ktime) + 21564000)*60
    return datetime.utcfromtimestamp(_)

def dict_to_list(my_dict):
    return sorted([(j,my_dict[j]) for j in my_dict], key=lambda x: x[0])

def kdatetosql(my_date):
    #turns keepa date to sql date
    my_date=str(my_date)
    if len(my_date)==8:
        return my_date[:4] + '-' + my_date[4:6] + '-' + my_date[6:8]
    elif len(my_date)==6:
        return my_date[:4] + '-' + my_date[4:6] + '-' + '01'
    elif len(my_date)==4:
        return my_date[:4] + '-' + '01' + '-' + '01' 
    else:
        return '2001-01-01'
    
def bbx_pct(bbx_lst, my_date,tp):
    #finds how much amn hogs buybox
    my_match = 'A3P5ROKL5A1OLE'
    temp_list = []
    for item in bbx_lst:
        if item[0].date() >= my_date - timedelta(tp) and item[0].date()<=my_date:
            temp_list.append(item)
    if len(temp_list)==0:
        return np.nan
    try:
        pct = Counter(elem[1] for elem in temp_list)[my_match]/len(temp_list)
    except:
        pct = 0
    return pct

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