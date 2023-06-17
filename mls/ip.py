from mlsapp.utils import *
from mlsapp.models import *
import requests
import numpy as np
import json
from bs4 import BeautifulSoup
import time
import random

def get_one_page(page_number=1):
    #get's one page from wholsaler b - isbn13, title, buy px
    my_r = requests.get(config('wholesaler_b_url') + str(page_number))
    temp_list = find_isbn_title_px(my_r)
    
    return temp_list

def look_up_page(page_list):
    #looks up info on isbns for page in the apis
    ret = []
    for item in page_list:
        temp_isbn = item[0]
        if not isValidISBN13(temp_isbn):
            pass
        else:
            #go to api one and get author, cover, pubdate and publisher
            d = find_dims(temp_isbn)
            ret.append([temp_isbn] + d + [item[2]])
            time.sleep(0.75)
    return  ret

def load_one_static(i,ws,md=date.today()):
        try:
            s = static(isbn13 = i[0], title = i[1][:200],
                        pubdate = f'{i[2].year}-{"{:02d}".format(i[2].month)}-{"{:02d}".format(i[2].day)}',
                        author = i[3], pubber = i[4], cover = i[5],
                        height = i[6], width = i[7], thick = i[8], weight = i[9],)
            s.save()
            print(f'{i[0]} loaded to static')
            try:
                c = catalogue(book = static.objects.filter(isbn13=i[0])[0], 
                buypx = i[10], wholesaler = ws, 
                date = f'{md.year}-{"{:02d}".format(md.month)}-{"{:02d}".format(md.day)}')

                c.save()
                print(f'{i[0]} loaded to catalogue')
            except:
                print(f'could not load catalogue data for {i}')
        except:
            print(f'could not load static data for {i}')

def look_and_load(ws=config('wholesaler_b')):
    #look up all wholesaler b and look up static data from api 1
    for i in range(75):
        _ = get_one_page(i)
        temp = look_up_page(_)
        for t in temp:
            load_one_static(t,ws=ws,md=date.today())

def load_rank(ws = config('wholesaler_b'), cat_date = '2021-10-08'):
    #
    isbns = [x['book_id'] for x in catalogue.objects.values('book_id').filter(wholesaler=ws, date=cat_date)]
    for i in isbns:
        try:
            load_one_sr(i)
        except:
            print(f'could not load {i}')

def load_one_sr(my_isbn, md=date.today()):
    d = get_one(my_isbn)
    offs=[]
    for item in list(d.keys()):
        if 'offer_' in item:
            offs.append(item)
    sellpx_list = [d[x][0] for x in offs]
    sell_list = [d[x][4] for x in offs]
    s = salesrank(book = static.objects.filter(isbn13=my_isbn)[0],
    sr = d['bsr'],
    date = f'{md.year}-{"{:02d}".format(md.month)}-{"{:02d}".format(md.day)}',
    rating = d['rating'], reviews = d['reviews'], offers = d['offers'],
    a_off = d['amzn_offer'], a_bb = d['amzn_bb'], a_px = d['amzn_px'], a_dims = d['dims'],
    sellers = sell_list, sell_prices = sellpx_list)
    s.save()

def find_isbn_title_px(my_request):
    #parses page from wholesaler b
    soup = BeautifulSoup(my_request.text, 'html.parser')
    isbns = []
    for x in soup.find_all('small'):
        isbns.append([x.get_text().strip().replace('ISBN ','')])
        my_list=[]
    counter = 0
    temp = []
    for x in soup.find_all('strong'):
        if x.get_text().strip()=='Item is liable for VAT':
            pass
        else:
            counter +=1
            temp.append(x.get_text().strip())
            if counter % 3 == 0:
                if temp !=[]:
                    my_list.append(temp)
                temp = []
    my_list = [[y[0],float(y[2].replace('Our Price:\n\n£',''))] for y in my_list]
    for i in range(len(isbns)):
        isbns[i] = isbns[i] + my_list[i]
    return isbns   

def add_one_api(my_isbn, my_dict):
    offs = []
    for item in list(my_dict.keys()):
        if 'offer_' in item:
            offs.append(item)
    sellpx_list = [my_dict[x][0] for x in offs]
    sell_list = [my_dict[x][4] for x in offs]
    p = apidata(isbn13= promo.objects.filter(isbn13=my_isbn)[0],
                bsr = my_dict['bsr'],
                pages = my_dict['pages'], 
                dims = my_dict['dims'], asin = my_dict['asin'], rating = my_dict['rating'],
                reviews = my_dict['rating'], offers = my_dict['offers'], 
                amzn_off = my_dict['amzn_offer'], amzn_bb=my_dict['amzn_bb'], amzn_px = my_dict['amzn_px'],
                sell_prices = sellpx_list, sellers = sell_list)
    p.save()

def get_one(my_isbn, bsr_cutoff=400000):
    print(my_isbn)
    try:
        i10 = toISBN10(my_isbn)
    except:
        return print('invalid isbn')
    try:
        prod_deets = get_deets(i10, srchtype='product')['product'] 
        try:
            bsr = prod_deets['bestsellers_rank'][0]['rank']
            print(type(bsr), bsr)
        except:
            bsr = 0
        try:
            pages = prod_deets['specifications'][2]['value']
        except:
            pages = ''
        try:
            dims = prod_deets['specifications'][5]['value']
        except:
            dims = ''
        x = {'bsr' : bsr, 'pages' : pages, 'dims' : dims}
    except:
        x = {'bsr' : 0, 'pages' : '', 'dims' : ''}
    try:
        
        if x['bsr'] < bsr_cutoff and x['bsr'] != 0:
            try:
                deets = get_deets(i10)
            except:
                deete = np.nan
            try:
                y = parse_details(deets)
            except:
                y = {'asin': i10, 'rating': 0, 'reviews': 0, 'offers': 0, 'offer_1': ['not found',0,0,0,0], 
                'amzn_offer': False, 'amzn_bb': False, 'amzn_px': 0}
        else:
            y = {'asin': i10, 'rating': 0, 'reviews': 0, 'offers': 0, 'offer_1': ['not found',0,0,0,0], 
                'amzn_offer': False, 'amzn_bb': False, 'amzn_px': 0}
    except:
        x['bsr']=0
        y = {'asin': i10, 'rating': 0, 'reviews': 0, 'offers': 0, 'offer_1': ['not found',0,0,0,0], 
                'amzn_offer': False, 'amzn_bb': False, 'amzn_px': 0}

    
    if x['bsr']=='nan':
        x['bsr'] = 0
    return (x | y)

def get_deets(an_asin,srchtype='offers', offer_id=0):
    params = {
      'api_key': config('api_key'),
        'type': srchtype,
      'output': 'json',
      'asin': an_asin,
     'amazon_domain': 'amazon.co.uk',
        'offers_condition_new': 'true'
    }
    if offer_id!=0:
        params['offer_id']=offer_id

    # make the http GET request to API
    api_result = requests.get(config('api_url'), params)

    # print the JSON response from Rainforest API
    return json.loads(json.dumps(api_result.json()))
    
def parse_details(my_deets):
    d=my_deets
    ret = { 'asin' : d['product']['asin']}
    try:
            ret['rating'] = d['product']['rating']
    except:
        ret['rating'] = 0
    try:
            ret['reviews'] = d['product']['reviews_total']
    except:
        ret['reviews'] = 0
    try:
        ret['offers'] = d['pagination']['offers_count']
    except:
        ret['offers'] = 0
    has_amzn_offer = False
    amzn_is_buy_box = False
    amzn_price = 0
    for i in range(len(d['offers'])):
        offer = d['offers'][i]
        price = offer['price']['value'] + offer['delivery']['price']['value']
        #logic to add missing postage
        if i==0:
            p1 = price
        if i==1:
            p2 = price
        if i > 1:
            if price < p1 and price < p2:
                price += 2.8
        try:
            is_buy_box = bool(offer['buybox_winner'])
        except:
            is_buy_box = False
        if is_buy_box:
                buy_box_price = price 
        is_fba = bool(offer['delivery']['fulfilled_by_amazon'])
        is_prime = bool(offer['is_prime'])
        seller = d['offers'][i]['seller']['name']
        if seller == 'Amazon':
            has_amzn_offer = True
            amzn_price = price
        if seller == 'Amazon' and is_buy_box:
            amzn_is_buy_box = True
        ret[f'offer_{i+1}'] = [price, is_buy_box, is_fba, is_prime, seller]     
    ret['amzn_offer'] = has_amzn_offer
    ret['amzn_bb'] =  amzn_is_buy_box   
    ret['amzn_px'] =  amzn_price
    return ret