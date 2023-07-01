import pandas as pd
import numpy as np
from datetime import date, timedelta
from mlsapp.models import Offers, WSInfo

def ubot(ws):
    #takes offers table and turns it into dataframe
    query = Offers.objects.filter(wholesaler=ws)
    ws_info = WSInfo.objects.filter(wholesaler=ws)[0]
    df = pd.read_excel('mls/offer_csvs' + ws_info.wholesaler + '.xlsx')
    df['ISBN'] = df['ISBN'].apply(str)
    current_isbns = list(set(df66['ISBN']))
    isbns_with_data = query.values_list('book_id', flat=True)
    frame_list = {}
    stat_list = []

    for qq in query:
        q = qq.jf
        isbn = qq.book_id

        if isbn not in current_isbns:
            continue

        print(isbn)

        if isbn not in isbns_with_data:
            continue

        sr = q['csv'][3]
        if sr is None or len(sr) <= 2:
            continue

        name = q['title']
        amzn_px = pel(q['csv'][0], sr)
        offers = pel(q['csv'][11], sr)
        newfba = pel(q['csv'][10], sr)
        newfbm = pel(squash(q['csv'][7]), sr)
        bb = pel(bbx_bool(q['buyBoxSellerIdHistory']), sr)
        pubdate = kdatetodate(q['publicationDate'])
        pubyrs = (date.today() - pubdate) / timedelta(365)

        try:
            fbafees = q['fbaFees']['pickAndPackFee'] / 100
        except:
            fbafees = 2.2

        try:
            weight = q['itemWeight']
        except:
            weight = 750

        inboundtransfee = 4 * weight / 14000
        fba_and_inbound = fbafees + inboundtransfee
        col_list = [offers, amzn_px, newfba, newfbm, bb]
        formatted_lists = [avgmaker(x, as_list=False) for x in [sr] + col_list]
        df = pd.DataFrame.from_dict(formatted_lists[0], orient='index')
        df = df.sort_index()

        for i in range(1, len(formatted_lists)):
            df[i] = df.index.map(formatted_lists[i])

        df.columns = ['sr', 'offers', 'amzn_px', 'newfba', 'newfbm', 'bb']
        buypx = df[df['ISBN']==isbn]['Price'].iloc[0]*op_dict[my_ws]['price_mult']
                    df['min_px'] = make_min_px_col(df)
                    df['sr'] = df['sr'].interpolate()
                    df['sr'] = df['sr'].fillna(method="ffill")
                    df['min_px'] = df['min_px'].interpolate()
                    df['bb'] = df['bb'].interpolate()
                    df['bb'] = df['bb'].fillna(method="ffill")
                    last_price = gnn(df['min_px'])
                    sr90 = df['sr'].iloc[-3:].mean()
                    bb90 = df['bb'].iloc[-3:].mean()
                    azpct = 0.053 if last_price < 5 else 0.153
                    
                    azfees = (azpct * last_price) + 1
                    all_costs_per = -(azfees + fba_and_inbound)
                    mgn = (last_price-buypx+all_costs_per)/buypx
                    
                    nd = novdec(formatted_lists[0])
                    
                    stat_list.append([isbn, name, gnn(df['sr']), sr90, df['sr'].mean(), df['sr'].std(), df['sr'].min(), df['sr'].max(), pubyrs, gnn(df['offers']),mgn,
                                                        last_price, all_costs_per, buypx, gnn(df['bb']),bb90] + nd)
                    frame_list[isbn] = df
                        #except:
                            #frame_list[isbn] = df
        ret_df = pd.DataFrame(stat_list)
        ret_df.columns = ['isbn','title','30d','90d','alltime','std','min','max','pubyrs', 'offers','exp_mgn', 
                                                        'min_px', 'all_costs_per', 'wavg_cost','bb30','bb90','nonxmas','xmas']
        ret_df.to_csv(op_dict[my_ws]['save_string'])
        return frame_list, stat_list

            
        
        
def parse_kcsv(q_line):
    d = {}
    pass

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

def gnn(my_series,n=1):
    #get's the last non np.nan entry in series or returns -1 if there are none
    if n>len(my_series):
        return -1
    my_entry = my_series[-n]
    if not pd.isna(my_entry):
        return my_entry
    n = n+1
    return gnn(my_series,n)

def kdatetodate(my_date):
    #turns pubdate string into date object
    my_date=str(my_date)
    if len(my_date)==8:
        return date(int(my_date[:4]),int(my_date[4:6]),int(my_date[6:8]))
    elif len(my_date)==6:
        return date(int(my_date[:4]),int(my_date[4:6]),1)
    elif len(my_date)==4:
        return date(int(my_date[:4]),1,1)
    else:
        return date(2001,1,1)

def bbx_pct(bbx_lst, my_date,tp):
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

def bbx_bool(bbx_lst):
    ret=[]
    my_match = 'A3P5ROKL5A1OLE'

    try:
        for i in range(len(bbx_lst)):
            if i%2==0:
                ret.append(bbx_lst[i])
            else:
                if bbx_lst[i] == my_match:
                    ret.append(1)
                else:
                    ret.append(0)
    except:
        pass
    return ret

def make_min_px_col(df):
    #makes a min px col using three price cols and wavg cost and allcosts per
    min_px_list = []
    for i in range(len(df)):
        min_px = np.inf
        for item in df[['newfba','newfbm','amzn_px']].iloc[i]:
            if item < min_px and item >0:
                min_px = item     
        if min_px==np.inf:
            min_px = np.nan
        min_px_list.append(min_px/100)
    return min_px_list

def pel(some_list, my_sr):
    #populates an empty list with sr dates and zeros
    if some_list is not None:
        return some_list
    else:
        return [0 if i%2 else x for i,x in enumerate(my_sr)]
        
def novdec(ts):
    #avg of sr in non novdec and novdec
    nondecnov = []
    decnov = []
    for item in ts:
        if item.month not in [11,12]:
            nondecnov.append(ts[item])
        else:
            decnov.append(ts[item])
    try:
        nondecnov_avg = mean([x for x in nondecnov if x == x])
    except:
        nondecnov_avg = np.nan
    try:
        decnov_avg = mean([x for x in decnov if x == x])
    except:
        decnov_avg = np.nan
    return [nondecnov, decnov_avg]

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

def dict_to_list(my_dict):
    return sorted([(j,my_dict[j]) for j in my_dict], key=lambda x: x[0])

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