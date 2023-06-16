#get date and number only from invoice
import tabula
import pandas as pd
import numpy as np
import PyPDF2
import re

def get_date_num(my_doc , area_params = [172,240,252,324],my_ws='a'):
    
    object = PyPDF2.PdfReader(my_doc)
    PageObj = object.pages[0]
    Text = PageObj.extract_text()
    inv_find = re.compile('(?:Invoice:\s*|Invoice # |Inv Num:|\nNo\. |Invoice Number[ \t]+|INVOICE\s*|Invoice Date\s*\d{1,2}/\d{2}/\d{4}|InvoiceNumber\n)([0-9]*)')
    date_find = re.compile('(?:Date:\s*|Invoice Date\s*|InvoiceDate\s*|YOUR DUES)(\d{1,2}/\d{2}/\d{4}|\d{1,2} [A-Za-z]{3} \d{1,2}|\d{2}/\d{2}/\d{2}|\d{1,2}[A-Za-z]{3}\d{4}|)')
    if my_ws=='moon':
        inv_find = re.compile('(?:InvoiceNumber\s*)(SI-[0-9]*)')
    try:
        my_num = inv_find.findall(Text)[0]
        my_date = date_find.findall(Text)[0]
        print(my_num)
        try:
            my_num = int(my_num)
        except:
            my_num = int(inv_find.findall(Text)[1])

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
     
    return my_date, my_num
