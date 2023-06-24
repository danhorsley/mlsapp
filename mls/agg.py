import pandas as pd
import statistics 
import numpy as np
from datetime import timedelta, date, datetime
from mlsapp.models import *
from mlsapp.utils import date_to_sql
import csv
from django.db.models import F, Count, Sum, Max, Min, FloatField, Avg, StdDev

def aggf():
    #first aggregate invoice data into total bought, price, first buy, last buy
    #merge with sales data aggregated by item, first buy, last buy
    #finally add active/non active
    #add lost/spoiled to balance
    invoice_agg = InvoiceData.objects.values('book_id','title').order_by('book_id')\
                .annotate(total_inv_cost=Sum(F('cost')*F('quantity')))\
                .annotate(total_inv_qty=Sum(F('quantity')))\
                .annotate(wavg_cost = (F('total_inv_cost')/F('total_inv_qty')))

    sales_agg = SalesData.objects.values('book_id').order_by('book_id')\
                                    .annotate(total_s=Sum('price'))\
                                    .annotate(total_pc=Sum('post_crd'))\
                                    .annotate(total_q=Sum('quantity'))\
                                    .annotate(total_f=Sum('salesfees'))\
                                    .annotate(total_post=Sum('postage'))
    isbns = list(set([x[0] for x in InvoiceData.objects.all().values_list('book_id')]))
    minmax = {y:InvoiceData.objects.filter(book_id=y).aggregate(Min('date'),Max('date')) for y in isbns}
    firstlast = {z:SalesData.objects.filter(book_id=z).aggregate(Min('date'),Max('date')) for z in isbns}
    firstbuy = {x:minmax[x]['date__min'] for x in minmax}
    lastbuy = {x:firstlast[x]['date__max'] for x in firstlast}
    dfi = pd.DataFrame.from_dict(invoice_agg)                                
    dfs = pd.DataFrame.from_dict(sales_agg)
    fdf = dfi.merge(dfs,how='inner',right_on='book_id',left_on='book_id')
    fdf['first_buy'] = fdf['book_id'].map(firstbuy)
    fdf['last_buy'] = fdf['book_id'].map(lastbuy)
    fdf['last_buy'] = np.where(fdf['last_buy'] is None, date.today(), fdf['last_buy'].dt.date)
    
    
    #next line is temporary adjustment for FBA cost of 0.3.  will adjust to weight related and merchant/fba fulfilled at later date
    
    actskus = active_skus()
    fdf['active'] = fdf['book_id'].isin(actskus)
    fdf['roi_date'] = np.where(fdf['active'], date.today(), pd.to_datetime(fdf['last_buy']).dt.date)
    #fdf['ann_rtn'] = 100*(fdf['pct_rtn']/100+1)**(1/((fdf['roi_date']-fdf['first_buy'])/timedelta(365)))
    for col in ['fmt', 'wt', 'pubdate','cat']:
        fdf[col] = fdf['book_id'].map(create_fxd(col))
    fdf['inboundfba'] = np.where(fdf['wt']==-1,0.35, 4 * (fdf['wt']/14000))
    fdf['net_profit'] = fdf['total_s'] + fdf['total_pc'] + fdf['total_post']+ fdf['total_f'] - fdf['total_inv_cost'] - (fdf['inboundfba']*fdf['total_q'])
    fdf['pubdate'] = pd.to_datetime(fdf['pubdate']).dt.date
    
    fdf['trd_profit'] = fdf['total_s'] + fdf['total_pc'] + fdf['total_post']+ fdf['total_f'] - ((fdf['wavg_cost'] + fdf['inboundfba']) *fdf['total_q'])
    #fdf['pct_rtn'] = 100*fdf['trd_profit']/(fdf['wavg_cost']*fdf['total_q']) 
    #fdf['dtfr'] = (fdf['roi_date']-fdf['first_buy']) * 100 / (fdf['pct_rtn'] * timedelta(1))
    fdf['days_active'] = (fdf['roi_date'] - fdf['first_buy'])/timedelta(1)
    fdf['AROInv'] = ((fdf['trd_profit']/fdf['total_inv_cost']+1)**(365/fdf['days_active']))-1
    fdf['all_costs_per'] =  - fdf['inboundfba'] + (fdf['total_post']+ fdf['total_f'])/fdf['total_q']
    stripdf = fdf[['book_id', 'title', 'trd_profit', 'net_profit','first_buy', 'roi_date', 'days_active', 'total_inv_cost', 'AROInv',
                     'total_q', 'fmt', 'pubdate','cat','wavg_cost','all_costs_per']]
    return fdf, stripdf

def create_avgs(my_isbn,my_date):
    #find closest month ends and previous 2 month ends
    #then get average for all time using different search
    dates = [date_to_sql(y) for y in [lme(my_date), lme(my_date,2) , lme(my_date,3)]]
    avgs = [x.salesrank for x in KeepaMAVG.objects.filter(book_id = my_isbn, date__in=dates)]
    temp_query = KeepaMAVG.objects.filter(book_id = my_isbn, date=lme(my_date))
    nf = denoner([x.newfba for x in temp_query])
    nm = denoner([x.newfbm for x in temp_query])
    az = denoner([x.AZpx for x in temp_query])
    bb30 = denoner([x.AZBBpct30 for x in temp_query])
    bb90 = denoner([x.AZBBpct90 for x in temp_query])
    if nf[0]==az[0]==nm[0]:
        nf,nm,az = find_last_non_zero_px(my_isbn, my_date)
    try:
        offerct = KeepaMAVG.objects.filter(book_id = my_isbn, date = lme(my_date))[0].offerct
    except:
        offerct = 0
    avg, std, mx, mi = avg_std_mm(my_isbn)
    try:
        return {'30d' :avgs[0], '60d' :(avgs[1] + avgs[0])/2, '90d' : sum(avgs)/3, 'alltime' : avg, 
                    'std': std, 'min': mi, 'max': mx, 'offers' : offerct, 
                    'newfba':nf[0], 'AZpx':az[0],  'newfbm' : nm[0],
                    'bb30': bb30[0],'bb90':bb90[0]}
    except:
        return {'30d' :np.nan, '60d' :np.nan, '90d' : np.nan, 'alltime' : np.nan, 
                    'std': np.nan, 'min': np.nan, 'max': np.nan, 'offers' : np.nan,
                    'newfba' : np.nan,  'AZpx':np.nan, 'newfbm':np.nan,
                    'bb30': np.nan,'bb90':np.nan}

def denoner(my_item):
    if my_item is None or my_item==[]:
        return [0]
    else:
        return my_item

def find_last_non_zero_px(my_isbn, my_date):
    for i in range(2,24):
        try:
            temp_query = KeepaMAVG.objects.filter(book_id = my_isbn, date=lme(my_date,i))
            nf = denoner([x.newfba for x in temp_query])
            nm = denoner([x.newfbm for x in temp_query])
            az = denoner([x.AZpx for x in temp_query])
            if not nf[0]==az[0]==nm[0]:
                return nf,nm,az
        except:
            pass
    return 0,0,0


def avg_std_mm(my_isbn):
    my_list = []
    #given rank query from KeepaMAVG returns "cleaned" avg, min, max and stdev
    #cleaning involves stripping out exagerated values at the beginning pre pub
    #scan first 5 items and if any over 2m then remove them
    query = list(KeepaMAVG.objects.filter(book_id=my_isbn).values_list('salesrank',flat=True))
    if len(query)>0:
        for item in query[:5]:
            if item>2000000:
                query.remove(item)
        return statistics.mean(query), statistics.stdev(query), max(query), min(query)
    else:
        return -1,-1,-1,-1

def create_analysis(save_to_csv=True):
    pd.set_option('display.float_format', lambda x: '%.1f' % x)
    pd.options.mode.chained_assignment = None
    df, sdf = aggf()
    extra_cols = ['30d', '60d','90d','alltime','std', 'min','max','offers', 'newfba', 'newfbm', 'AZpx','bb30','bb90']
    sdf = sdf.reindex(columns=['book_id','title','trd_profit', 'net_profit','first_buy','roi_date', 'days_active', 'total_inv_cost','AROInv',
                                'fmt','pubdate','cat','total_q','wavg_cost','all_costs_per'] + extra_cols)
    for i in sdf.index:
        dats = create_avgs(sdf['book_id'][i], sdf['first_buy'][i])
        print(i,dats, sdf.head())
        for my_key in dats:
            sdf[my_key][i] = dats[my_key]
    sdf['title'] = sdf['title'].str.slice(0,60)
    if save_to_csv:
        sdf.to_csv('analysisframe.csv')
    return sdf

def create_fxd(my_col):
    #gather fixed dataframe of genre, sub genre and format
    if my_col != 'cat':
        return  {v['book_id']:v[my_col] for v in KeepaDataFXD.objects.all().values()}
    else:
        ret = {}
        for v in KeepaDataFXD.objects.all().values():
            try:
                ret[v['book_id']] = strip_cats(v[my_col])[0]
            except:
                ret[v['book_id']] = 'Unknown'
    return ret
        #return  {v['book_id']:strip_cats(v[my_col])[0] for v in KeepaDataFXD.objects.all().values()}
    

def strip_cats(query_line):
    return [v['name'] for v in query_line][2:]


def lme(my_date, go_back=1):
    #return previous month end last day : give and receive in date format
    md = my_date.replace(day=1) - timedelta(1)
    gb = go_back - 1
    if gb != 0:
        md = lme(my_date = md, go_back = gb)
    return md

def active_skus():
    #activeskus = []
    #sku_dict = {i[2] : i[1] for i in SkuMap.objects.filter(status='Active').values_list()}
    # with open(f"mlsapp/agg/activeskus.csv", "r", encoding="ISO-8859-1") as f:
    #         rows = csv.reader(f)
    #         for row in rows:
    #             try:
    #                 activeskus.append(sku_dict[row[0]])
    #             except:
    #                 pass
    #return activeskus     
    return [z[0] for z in SkuMap.objects.filter(status='Active').values_list('book_id')]       