from decouple import config
from datetime import date
import csv
import time
import requests
from bs4 import BeautifulSoup


def get_h(r1=0,r2=79):
    all_items =[]
    for page_number in range(r1,r2):
                try:
                    print(page_number)
                    my_r = requests.get(config('wholesaler_b_url') + str(page_number))
                    #print(page_number, type(my_r), parse_page(my_r, self.ws))
                    all_items += parse_b(my_r)
                    time.sleep(5)
                except:
                    pass
    with open(f"hardwick_scrape.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(all_items)
    return print('csv created')
                

def  parse_b(page):
    soup = BeautifulSoup(page.text, 'html.parser')
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
    my_rrps = [na_to_0(z.next_sibling.strip('\n').replace('£','')) for z in soup.find_all('strong')[1::3]]
    for i in range(len(isbns)):
        isbns[i] = isbns[i] + my_list[i] + [my_rrps[i]]
    return isbns   

def na_to_0(my_string):
    if my_string in ['N/A',''] : return 0
    return float(my_string)