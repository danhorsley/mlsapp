from mlsapp.models import Offers, static, WSInfo
from mlsapp.utils import toISBN10, date_to_sql, null_to_blank, find_dims, find_sleep_time
from datetime import date, time
import pandas as pd
import requests
import ast

def offpop():
    #pops offers model
    #TODO get df.colums to read the dict from WS Info
    #TODO add a is_live logic checker
    #TODO get  read_excel path from WSInfo
    #TODO fix logic on counter of sleep time
    WSI_query = WSInfo.objects.all()
    for i in len(range(WSI_query)):
        df = pd.read_excel(f'mls/offer_csvs/{WSI_query[i].wholesaler}.xlsx')
        df = pd.read_excel('mlsapp/66full.xlsx')
        df.columns= ['ISBN', 'Pack Qty', 'Title', 'Format',  'Available Stock',
        'Author', 'Cover Price', 'RRP', 'Imprint', 'Category 1', 'Category 2',
        'Unnamed: 12']
    isbns66 = [str(x) for x in list(set(list(df['ISBN'])))]
    api_url = "https://api.keepa.com/"
    my_date = date_to_sql(date.today())
    isbns_to_add=[]
    existing_keepa = [x[0] for x in Offers.objects.all().values_list('book_id')]
    for isb in isbns66:
        if isb not in existing_keepa and isb[:3]=='978':
            isbns_to_add.append(isb)
    print('number of names to add is ', len(isbns_to_add))
    for isbn in isbns_to_add:
        try:
            my_asin = toISBN10(isbn)
            print(isbn, my_asin)
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

            req = requests.get(api_url + f"product?key={config('k_api_key')}&domain=2&asin={my_asin}&buybox=1&offers=20")
            sleep_time = find_sleep_time(req)
            _ = Offers(book= my_book_id, jf = req.json()['products'][0], date = my_date)
            _.save()
            time.sleep(sleep_time)
        except:
            print(f"could not add {isbn}")
            pass