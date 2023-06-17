#extract and upload sales data to new model
from mlsapp.models import *
from mlsapp.utils import *
#import os
import csv
import pytz
from datetime import datetime
from django.db.models import F, Count, Sum


def pop_sales(reset = True):
    sku_dict = {i[2] : i[1] for i in SkuMap.objects.all().values_list()}
    cost_dict = wac_dict()
    if reset:
        SalesData.objects.all().delete()
    with open("mlsapp/s_get/sd.csv", "r") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row[4]=='':
                    pass
                else:
                    if float(row[23]) == 0 : 
                        my_postage = -2.8
                    else : 
                        my_postage = row[23]
                    sd = SalesData(book = static.objects.filter(isbn13=sku_dict[row[4]])[0],
                                    date = datetime.strptime(row[0], '%d %b %Y %H:%M:%S %Z').replace(tzinfo=pytz.UTC), 
                                    quantity = row[6], price = row[13], post_crd = row[15],
                                    salesfees = row[22], postage = my_postage, 
                                    wac = -cost_dict[sku_dict[row[4]]][2], 
                    profit = float(row[13])+float(row[15])+float(row[22])+float(my_postage)-cost_dict[sku_dict[row[4]]][2])
                    sd.save()

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