from ast import excepthandler
from mlsapp.models import *
import pytz
import csv
import re
from datetime import datetime
from django.db.models import F, Count, Sum

avoid = ['M5-5WGJ-EUJD']

def spop():
    #get all invoice isbns
    #agg sales for each name using skumap (one to many)
    #function to work out weighted average cost
    sku_dict = {i[2] : i[1] for i in SkuMap.objects.all().values_list()}
    rejects = []
    wd = wac_dict()
    with open("mls/sd/sd.csv", "r") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row[4]=='' or row[4] in avoid:
                    pass
                else:
                    # try:
                        if float(row[23]) == 0 and 'Adjustment' not in row[2] and 'Refund' not in row[2]: 
                            my_postage = -2.8
                        else : 
                            my_postage = float(row[23])
                        if 'Sept' not in row[0]:
                            my_date = datetime.strptime(row[0], '%d %b %Y %H:%M:%S %Z').replace(tzinfo=pytz.UTC)
                        else:
                                my_date = datetime.strptime(re.sub('Sept','Sep',row[0]), '%d %b %Y %H:%M:%S %Z').replace(tzinfo=pytz.UTC)
                        my_price = (float(row[13])+float(row[25]))/float(row[6])
                        try:
                            www = -wd[sku_dict[row[4]]][2]
                            sd = SalesData(book = static.objects.filter(isbn13=sku_dict[row[4]])[0],
                                            date = my_date, 
                                            quantity = int(row[6]), 
                                            type = row[2],
                                            order_id = row[3],
                                            price = my_price, post_crd = float(row[15]),
                                            salesfees = float(row[22]), postage = my_postage, 
                                            wac = -wd[sku_dict[row[4]]][2], 

                            profit = my_price*float(row[6])+float(row[15])+float(row[22])+float(my_postage)-wd[sku_dict[row[4]]][2])
                            sd.save()
                        except:
                            print(row)
                    # except KeyError:
                    # except Exception as e:
                    #     print(f"could not add {row[4]} due to {e}")
                    #     try:
                    #         rej_isbns = [x[0] for x in rejects]
                    #     except:
                    #         rej_isbns = []
                    #     #print(rej_isbns, row[4])
                    #     if row[4] not in rej_isbns:
                    #         rejects.append([row[4],row[5]])
                    #     return rejects

def wac_dict(my_how = 'isbn'):
    if my_how == 'title': my_how = 'book_id__title'
    if my_how == 'isbn': my_how = 'book_id'
    invoice_agg = InvoiceData.objects.values(my_how).order_by(my_how)\
                .annotate(total_inv_cost=Sum(F('cost')*F('quantity')))\
                .annotate(total_inv_qty=Sum(F('quantity')))\
                .annotate(wavg_cost = (F('total_inv_cost')/F('total_inv_qty')))
    invoice_dict = {y[my_how][:21]:[y['total_inv_cost'], y['total_inv_qty'], 
                                y['wavg_cost']] for y in invoice_agg}
    return invoice_dict

    