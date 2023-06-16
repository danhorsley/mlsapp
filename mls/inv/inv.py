from django.forms import PasswordInput
import tabula
from decouple import config
from datetime import date, datetime
import pandas as pd
from mlsapp.models import *
from mlsapp.utils import find_dims, date_to_sql, isValidISBN13, null_to_blank, str_date_to_sql
from .dtnum import get_date_num
import re
import PyPDF2
import os

def inv_tidy():
    #change differing name to same name
    isbns = list(set([x[0] for x in InvoiceData.objects.all().values_list('book_id')]))
    for i in isbns:
        query = InvoiceData.objects.filter(book_id=i)
        name_list = [x[0] for x in query.values_list('title')]
        n = len(set(name_list))
        if n <= 1:
            pass
        else:
            anchor = query[0].title
            print(f'updating {anchor} as there are {n} different titles - isbn is {i}')
            for q in query[1:]:
                q.title=anchor
                q.save()

class iload:

    def __init__(self):
        self.d = date.today() #today's date
        #params are top, left, bottom and right 
        #params3 is just to get date and inv number
        #'e' : {'ws' :'Bookmark', 'params' : [252,25,612,576], 'style' : 'pdf'},
        self.ws_dict = {'a' : {'ws' :'Boon', 'params' : [288,72,792,540], 'params2' : [72,72,792,540], 
                                                    'params3' : [172,240,252,324], 'style' : 'pdf'},
                        'b' : {'ws' :'Hardwick', 'params' : [252,25,612,576], 'style' : 'xl'},
                        'c' : {'ws' :'Greenvale', 'params' : [252,25,612,576], 'params2' : [72, 288, 380.0, 410, 450.0, 500,545.0, 594.0],
                                                    'params3' : [144,396,200,560], 'style' : 'pdf'},
                        'd' : {'ws' :'Gardners', 'params' : [72*2,0,5.5*72,12*72], 'params2' : [72, 86.4, 252.0, 331.2, 432, 684.0, 734.4, 766.8],
                                                    'params3' : [1.5*72,0,2*72,12*72], 'style' : 'pdf'},
                        
                        'f' : {'ws' :'66', 'params3' : [108, 72, 151, 468], 'style' : 'pdf'},  #[126, 108, 151, 468]
                        'g' : {'ws' :'Octagon', 'params' : [4.05*72, 0, 9*72, 8.5*72], 
                                'params2' : [0.75*72, 1.75*72, 2.5*72, 5.5*72, 7*72,7.5*72],
                                'params3' : [3*72,2*72,3.5*72,8*72],'style' : 'pdf'},
                        'h' : {'ws': 'comb', 'params' : [252,25,612,576], 'style' : 'xl'},
                        'moon': {'ws': 'moonraker', 'params'  : [288,72,792,540], 'params2' : [72,72,792,540], 'params3' : [172,240,252,324], 'style' : 'pdf'},
                        'bs': {'ws': 'bestsellers', 'params'  : [288,72,792,540], 'params2' : [72,72,792,540], 'params3' : [172,240,252,324], 'style' : 'pdf'}}
        self.dodge = ['B07CL5KHVJ',	'B07CS7CDVC',	'B07CS33NSZ',	'B07CS33NSZ',	'B07DKHV41T',	'B07M7PGLZX',	'B07M7PGLZX',	'XDC349',	'B078YYHW4Z',	
        'B094JNPG47',	'B07C53MWXM',	'B07N36YS16',	'B085LMMNXC',	'NOTE056',	'NOTE056',	'B079FPCSKS',	'B00OV3ZY76']
                                

    def wipe_inv_db(self, which_ws ='all'):
        #DANGER DANGER DANGER - WIPES whole Invoice model
        if which_ws == 'all':
            InvoiceData.objects.all().delete()
            return print(f"all objects in InvoiceData deleted")
        else:
            InvoiceData.objects.filter(wholesaler=which_ws).all().delete()
            return print(f"all objects in InvoiceData with wholesaler {which_ws} deleted")

    def correct_isbn(self,my_isbn):
        if my_isbn in self.dodge:
            return my_isbn
        my_isbn = str(my_isbn)
        #checks if isbn is valid isbn13
        #if not can correct a limited number of error types
        #failing that prints warning
        if isValidISBN13(my_isbn):
            return my_isbn
        else:
            #first case is missing leading 9
            if my_isbn[0]=='7':
                my_isbn= '9' + my_isbn
                return self.correct_isbn(my_isbn)
            #second case is trailing last digit with a space
            elif re.match("\d{12} \d{1}",my_isbn) is not None:
                my_isbn = my_isbn[:12] + my_isbn[-1]  
                return self.correct_isbn(my_isbn)
            #third case is normal isbn with a trailing .0
            elif re.match("(\d{13}).0",my_isbn) is not None:
                my_isbn = str(int(float(my_isbn)))
                return self.correct_isbn(my_isbn)
            else:
                print(f"could not match {my_isbn}")
                return my_isbn + "_badisbn"


    def num_pages(self,doc):
        reader = PyPDF2.PdfReader(doc)
        return len(reader.pages)

    def find_new_inv(self,selection='all'):
        #******* WORKING ON THIS *********
        if selection == 'all':
            my_select = self.ws_dict.keys()
        else:
            my_select = [selection]
        for ws in my_select:
            if self.ws_dict[ws]['style']=='pdf':
                my_path = 'mls/inv/invpdfs/' + self.ws_dict[ws]['ws'].lower() + '_inv'
                invoice_list = os.listdir(my_path)
                existing_inv_nums = list(set([x[0] for x in InvoiceData.objects.filter(wholesaler = self.ws_dict[ws]['ws']).values_list('inv_num')]))
                for invoice in invoice_list:
                    my_doc = my_path +'/' + invoice
                    print(my_doc)
                    if '.DS_Store' in invoice:
                        pass
                    else:
                        my_date, inv_num = get_date_num(my_doc, area_params = self.ws_dict[ws]['params3'],my_ws=ws)
                        if inv_num in existing_inv_nums:
                            print(f'inv number {inv_num} already present')
                            pass           
                        else:
                            print(f'adding inv num {inv_num} for wholsaler {ws}')
                            temp_inv = self.read_tab(my_doc, ws)
                            for i in range(len(temp_inv)):
                                r = list(temp_inv.iloc[i])
                                self.save_to_model(r)
            elif self.ws_dict[ws]['style']=='xl':
                existing_inv_nums = list(set([x[0] for x in InvoiceData.objects.filter(wholesaler = self.ws_dict[ws]['ws']).values_list('inv_num')]))
                my_path = 'mls/inv/invpdfs/' + self.ws_dict[ws]['ws'].lower() + '_inv'
                invoice_xl = os.listdir(my_path)
                if '.DS_Store' in invoice_xl:
                    invoice_xl.remove('.DS_Store')
                tab = pd.read_excel(my_path + '/' + invoice_xl[0])
                for i in range(len(tab)):
                    r = list(tab.iloc[i])
                    if r[6] in existing_inv_nums:
                        pass
                    else:
                        self.save_to_model(r)
        
    
    def ext_dir(self,ws):
        if self.ws_dict[ws]['style']=='pdf':
            my_path = 'mlsapp/invs/invpdfs/' + self.ws_dict[ws]['ws'].lower() + '_inv'
            invoice_list = os.listdir(my_path)
            p_ones=[]
            for invoice in invoice_list:
                print(invoice)
                temp_inv = self.read_tab(my_path +'/' + invoice, ws)
                for i in range(len(temp_inv)):
                    r = list(temp_inv.iloc[i])
                    self.save_to_model(r)
                     
        elif self.ws_dict[ws]['style']=='xl':
            my_path = 'mlsapp/inv/invpdfs/' + self.ws_dict[ws]['ws'].lower() + '_inv'
            invoice_xl = os.listdir(my_path)
            if '.DS_Store' in invoice_xl:
                invoice_xl.remove('.DS_Store')
            tab = pd.read_excel(my_path + '/' + invoice_xl[0])
            for i in range(len(tab)):
                r = list(tab.iloc[i])
                self.save_to_model(r)
                
    def check_if_entry_exists():
        #checks if entry is already in the DB and returns a bool
        x=0
        return x
    
    def save_to_model(self,r):
            try:
                #print(f"searching for isbn {r[0]}")
                ci = self.correct_isbn(r[0])
                st = static.objects.filter(isbn13=ci)[0]
            except:
                #print(f"searching for isbn {r[0]}")
                ci = self.correct_isbn(r[0])
                dims = find_dims(ci)
                dims = [null_to_blank(dims[i],i) for i in range(len(dims))]
                s = static(isbn13 = ci, title = dims[0][:200],
                                pubdate = date_to_sql(dims[1]),
                                author = dims[2], pubber = dims[3], cover = dims[4],
                                height = dims[5], width = dims[6], thick = dims[7], weight = dims[8], rrp = 0)
                s.save()
                st = static.objects.filter(isbn13=ci)[0]
            #print(r)
            _ = InvoiceData(book = static.objects.filter(isbn13=ci)[0], 
            quantity = r[1], title = r[2], cost = r[3], totalprice = r[4], date = r[5], inv_num = r[6], wholesaler = r[7])
            _.save()   
            print(r, " saved to model ")

    def read_tab(self,my_doc, ws):
        
        my_date, inv_num = get_date_num(my_doc, area_params = self.ws_dict[ws]['params3'],my_ws=ws)

        if ws=='a': 
            tab = tabula.read_pdf(my_doc, pages='all',guess=False, area= self.ws_dict[ws]['params'],lattice=True) 
            if len(tab[0])==0:
                tab[0] = tabula.read_pdf(my_doc, pages=1,lattice=True)[1]
            tab[0]=tab[0].rename(columns = {'Item':'ISBN', 'Price':'cost', 'Total\rPrice\r(*)inc vat':'totalprice'})

        elif ws=='c':
            tab = tabula.read_pdf(my_doc, pages='all',guess=False, area= self.ws_dict[ws]['params'],columns = self.ws_dict[ws]['params2']) 
            tab[0] = drop_nas(tab[0])
            tab[0]['cost'] = tab[0]['Price']*0.5
            tab[0]['totalprice'] = tab[0]['cost'] * tab[0]['Qty']
            tab[0]=tab[0].rename(columns = {'ISBN/Bar Code':'ISBN'})
            tab[0] = tab[0][['ISBN','Qty','Title', 'cost', 'totalprice']]

        elif ws=='d':
            tab = tabula.read_pdf(my_doc, pages='all',guess=False, area= self.ws_dict[ws]['params'],columns = self.ws_dict[ws]['params2']) 
            tab[0] = tab[0][~tab[0]['AUTHOR'].isin(['GARDNERS BOOKS', 'gardners.com'])]
            tab[0] = drop_nas(tab[0])
            try:
                tab[0]['PRICE'] = pd.to_numeric(tab[0]['PRICE'])
            except:
                tab[0]['PRICE'] = pd.to_numeric(tab[0]['PRICE.1'])
            tab[0]['DISC'] = pd.to_numeric(tab[0]['DISC'])
            tab[0]['cost'] = tab[0]['PRICE']*(100 - tab[0]['DISC'])/100
            tab[0]=tab[0].rename(columns = {'ISBN QT':'ISBN', 'TITLE' : 'Title','VALUE': 'totalprice', 'Y':'Qty'})
            tab[0] = tab[0][['ISBN','Qty','Title', 'cost', 'totalprice']]

        elif ws=='f':
            print(my_doc)   
            tab = tabula.read_pdf(my_doc, pages=1,lattice=True)
            print(tab[3])
            column_find = tab[3].columns[5]
            tab[3] = tab[3][tab[3]['ISBN'].notna() & tab[3]['Order value'].notna()]   
            tab[3] = tab[3][~tab[3]['Order value'].isin(['£0.00'])]
            tab[3] = tab[3][tab[3][column_find]!='ck']   
            tab[0] = tab[3].copy()
            tab[0]['cost'] = pd.to_numeric(tab[0]['Cost\rprice'].str.replace('£', ''))
            try:
                tab[0][column_find]=tab[0][column_find].str.replace(" ","")
            except:
                pass
            tab[0]['Qty'] =  pd.to_numeric(tab[0][column_find])
            tab[0]['totalprice'] = tab[0]['cost'] * tab[0]['Qty']
            tab[0] = tab[0][['ISBN','Qty','Title', 'cost', 'totalprice']]

        elif ws=='g':
            tab = tabula.read_pdf(my_doc, pages=1, guess =False, 
                      area=self.ws_dict[ws]['params'], columns = self.ws_dict[ws]['params2'],
                      pandas_options = {'header': None})
            tab[0].columns = ['Qty','ignore','ISBN','Title','cost','totalprice', 'ignore2']
            tab[0] = tab[0][tab[0][tab[0].columns[0]].notna() & tab[0][tab[0].columns[1]].notna() & tab[0][tab[0].columns[3]].notna() & tab[0][tab[0].columns[5]].notna()]
            tab[0]['cost'] = tab[0]['cost'].map(lambda x: x.rstrip(' Each'))
            tab[0] = tab[0][['ISBN','Qty','Title','cost','totalprice']]

        elif ws=='bs':
            tab = tabula.read_pdf(my_doc)
            tab[0][['net_weight', 'ISBN']] = tab[0]['Net Weight (g) ISBN'].str.split(" ", expand = True)
            tab[0][['totalprice', 'vat']] = tab[0]['Net Total £ Vat%'].str.split(" ", expand = True)
            tab[0]=tab[0].rename(columns = {'Net £':'cost'})
            tab[0] = tab[0][['ISBN','Qty','Title','cost','totalprice']]

        elif ws=='moon':
            tab = tabula.read_pdf(my_doc)
            tab[0]=tab[0].rename(columns = {'Quantity':'Qty', 'Amount GBP':'totalprice'})
            tab[0] = tab[0][tab[0]['Qty'].notna()]
            tab[0][['ISBN', 'Title']] = tab[0]['Description'].str.split(" - ", n=1,expand = True)
            tab[0][['cost', 'vat']] = tab[0]['Unit Price VAT'].str.split(" ", n=1, expand = True)
            tab[0] = tab[0][['ISBN','Qty','Title','cost','totalprice']]

        n = self.num_pages(my_doc)
        if len(tab[0])==0:
            tab[0] = tabula.read_pdf(my_doc, pages=1,lattice=True)[1]
        tab[0]['cost'] = tab[0]['cost'].apply(lambda z:  numfix(z))
        tab[0]['totalprice'] = tab[0]['totalprice'].apply(lambda z:  numfix(z))
        all_pages = [drop_nas(tab[0])]
        #print(all_pages)
        if n>1:        
                try:
                    page_read = tabula.read_pdf(my_doc, pages='all',guess=False, area=self.ws_dict[ws]['params2'],lattice=True)
                    for i in range(2,n+1):
                        page_read[i] = drop_nas(page_read[i])
                        page_read[i].columns = all_pages[0].columns
                        all_pages.append(page_read[i])
                except:
                    pass
        ret = pd.concat(all_pages, ignore_index = True)
        if ws!='d' : ret['date'] = str_date_to_sql(my_date)
        else: 
            d = datetime.strptime(my_date, '%d/%m/%y')
            ret['date'] = f'{d.year}-{"{:02d}".format(d.month)}-{"{:02d}".format(d.day)}'
        ret['inv_num'] = inv_num
        ret['wholesaler'] = self.ws_dict[ws]['ws']
        
        print(ret)
        return ret

def drop_nas(frame):
    #drops vertical nan columns then any rows containing nan in cols 0&1
    frame = frame.dropna(axis = 1, how = 'all')
    frame = frame[frame[frame.columns[0]].notna() & frame[frame.columns[1]].notna() & frame[frame.columns[3]].notna()]
    return frame

def ri(my_path='b'):
    path_dict = {'b' : 'boon_inv', 'g' : 'greenvale_inv', '66': '66_inv'}
    invoice_list = os.listdir(path_dict[my_path])
    my_tables = []
    for invoice in invoice_list:
        print(invoice)
        if my_path=='g':
            #df_list = tabula.read_pdf(f"{path_dict[my_path]}/{invoice}", pages='all',multiple_tables=True, pandas_options = {'header': None})
            df_list = tabula.read_pdf(f"{path_dict[my_path]}/{invoice}", pages=1,guess=False, area=[252,25,612,576])
            mdf = df_list[0].copy()
            mdf[['code', 'Code Title']] = mdf['Code Title'].str.split(' ',1,expand=True)
            mdf.columns = ['Title', 'ISBN13','Qty','Price','Disc','Net','VAT','code']
            mdf = mdf.drop(mdf.index[[0]])
            mdf = mdf[mdf['ISBN13'].notna() & mdf['Qty'].notna()]
            mdf['ISBN13'] = mdf['ISBN13'].astype(int)
            my_tables.append(mdf)
        
        #sometimes picks up address etc as first
        else:
            df_list = tabula.read_pdf(f"{path_dict[my_path]}/{invoice}", pages='all')
            if len(df_list[0])!=0:
                df=df_list[0]
            else:
                df=df_list[1]
            
        
            if my_path=='b':
                df.columns=df.iloc[1]
            elif my_path=='66':
                df.columns=df.iloc[0]
            
            df = df.drop(df.index[[0,1]])
            df = df.reset_index(drop=True)
            my_tables.append(df)
    return my_tables

def deets_extract(my_doc,my_path):
    if my_path=='b':
        df = tabula.read_pdf(my_doc, pages=1,guess=False, area=[180,216,252,342],pandas_options = {'header': None})
        my_date = df[0][1][0]
        my_inv_num = df[0][1][0]
    return my_date, my_inv_num

def numfix(z):
    if isinstance(z,float):
        return True
    elif isinstance(z,int):
        return True
    else:
        return re.sub('[^0-9.]', '', z)