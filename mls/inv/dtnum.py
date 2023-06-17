#get date and number only from invoice
import tabula
import pandas as pd
import numpy as np
import PyPDF2
import re
from mlsapp.utils import numfix

def get_date_num(my_doc , area_params = [172,240,252,324],my_ws='a'):
    #gets invoice number and date from invoices in a really hacky way - try and come up with something better
    # try:
    object = PyPDF2.PdfReader(my_doc)
    # except:
    #     #this helps with hard to find EOF tags in java for pdfs
    #     my_doc_crop = reset_eof_of_pdf_return_stream(my_doc)
    #     object = PyPDF2.PdfReader(my_doc_crop)
    PageObj = object.pages[0]
    Text = PageObj.extract_text()
    inv_find = re.compile('(?:Invoice:\s*|Invoice # |Inv Num:|\nNo\. |Invoice Number[ \t]+|INVOICE\s*|Invoice Date\s*\d{1,2}/\d{2}/\d{4}|InvoiceNumber\n|Invoice Number\s*)([0-9]*)')
    date_find = re.compile('(?:Date:\s*|Invoice Date\s*|InvoiceDate\s*|YOUR DUES\s*)(\d{1,2}/\d{2}/\d{4}|\d{1,2} [A-Za-z]{3} \d{1,2}|\d{2}/\d{2}/\d{2}|\d{1,2}[A-Za-z]{3}\d{4}|)')
    if my_ws=='moon':
        inv_find = re.compile('(?:InvoiceNumber\s*SI-)([0-9]*)')
    try:
      
        my_num = inv_find.findall(Text)[0]
        my_date = date_find.findall(Text)[0]
        print(my_num)
        try:
            my_num = int(my_num)
            
        except:
            my_num = int(inv_find.findall(Text)[1])
            
        try:
            #catches if 66 inv in a strange format
            if my_ws == 'f' and my_date =='' or my_num=='':
                    tab = tabula.read_pdf(my_doc, pages=1, guess=False, area = area_params)
                    my_num = int(tab[0].columns[0][-5:])
                    my_date = tab[0].columns[1][-10:]
        except:
            pass
            

    except:
        tab = tabula.read_pdf(my_doc, pages=1, guess=False, area = area_params)
        if my_ws == 'a':
            my_date = tab[0].columns[1]
            my_num = int(tab[0][my_date][0])
        elif my_ws == 'f':
            my_num = int(tab[0].columns[0][-5:])
            my_date = tab[0].columns[1][-10:]
        elif my_ws =='g':
            print('error')
        try:
            #catches if octagon inv in a strange format
            #print("trigger**")
            if my_ws == 'g' and my_date =='' or my_num=='':
                    tab = tabula.read_pdf(my_doc, pages=1, guess=False, area = area_params)
                    my_num = int(tab[0].columns[0][-7:])
                    my_date = numfix(tab[0].columns[1][-8:]).lstrip()
        except:
            pass
    return my_date, my_num




# def reset_eof_of_pdf_return_stream(my_pdf):
#     with open(my_pdf, 'rb') as p:
#         txt = (p.readlines())
#     # find the line position of the EOF
#     for i, x in enumerate(txt[::-1]):
#         if b'%%EOF' in x:
#             actual_line = len(txt)-i
#             print(f'EOF found at line position {-i} = actual {actual_line}, with value {x}')
#             break

#     # return the list up to that point
#     return txt[:actual_line]