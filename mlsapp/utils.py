import re
from datetime import datetime, date
import ast
from decouple import config
import requests
import json
import time
import csv
from mlsapp.models import *

def date_to_sql(d):
    #returns datetime date as sql string date
      return f'{d.year}-{"{:02d}".format(d.month)}-{"{:02d}".format(d.day)}'


def find_dims(my_isbn):
    pounds_grams = 453.592
    inches_mm = 25.4
    h = {'Authorization': config('my_isbn_db_key')}
    try:
        resp = requests.get(f"https://api2.isbndb.com/book/{my_isbn}", headers=h)
        time.sleep(1)
        
        try:
            title = resp.json()['book']['title']
        except:
            title = 'unknown'
        try: 
            authors = resp.json()['book']['authors'][0]
        except:
            authors = 'unknown'
        try:
            binding = resp.json()['book']['binding']
        except:
            binding = 'unknown'
        try:
            pubdate = datetime.strptime(resp.json()['book']['date_published'],'%Y-%m-%dT%H:%M:%SZ').date()
        except:
            try:
                pubdate = datetime.strptime(resp.json()['book']['date_published'],'%Y').date()
            except:
                pubdate = date(2001,1,1)
        try:
            pubber = resp.json()['book']['publisher']
        except:
            pubber = 'unknown'
        try:
            x = '{' + resp.json()['book']['dimensions'].replace(' Inches','').replace(' Pounds','').replace('Height', "'Height'")\
                                                                        .replace('Length', "'Length'").replace('Weight',"'Weight'")\
                                                                        .replace('Width', "'Width'") + '}'
            temp_dict = ast.literal_eval(x)
            ret = [title, pubdate, authors, pubber, binding, temp_dict['Height']*inches_mm, temp_dict['Length']*inches_mm, 
                temp_dict['Width']*inches_mm, temp_dict['Weight']*pounds_grams]
            return ret
    
    
        except:
            return [title, pubdate, authors, pubber, binding, 0,0,0,0]

    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
        time.sleep(5)
        pass

def isOdd(n):
  #small utility for isbn13 check sum
  if n%2 == 0 :
    return False
  else:
    return True

def isValidISBN13(code):
  code = str(code)
  result = False
  #isbn13 has 13 chars
  #first 3 digits are 978
  #last digit matches check sum
  if code[0:3] == '978' and re.match('^\d{10}$', code[3:]):
    sum=0
    for i in range(0,12):
      sum += int(code[i]) * (3 if isOdd(i) else 1)
    result = (10 - (sum % 10)) % 10 == int(code[12])
    
  return result

def calcCheckDigitForISBN10(code):
  #take 9 digits from isbn13 and create check digit for an isbn10
  #isbn10 check sum weight goes down from from 10 to 2 from first digit to penultimate
  #check sum modulus is 11 with 10 represented by X
  code = code.replace("-","")
  sum = 0
  weight = 10
  for i in range(len(code)):
    sum += int(code[i]) * (weight - i)
  check = 11 - (sum % 11)
  if check == 10:
    check = 'X'
  if check == 11:
    check = 0
  return check

def isValidISBN13(code):
  result = False
  #isbn13 has 13 chars
  #first 3 digits are 978
  #last digit matches check sum
  if code[0:3] == '978' and re.match('^\d{10}$', code[3:]):
    sum=0
    for i in range(0,12):
      sum += int(code[i]) * (3 if isOdd(i) else 1)
    result = (10 - (sum % 10)) % 10 == int(code[12])
    
  return result
  
def toISBN10(isbn):
  isbn = str(isbn)
  code = ""
  if isValidISBN13(isbn):
  #converts ISBN13 to ISBN 10
    code = isbn[3:len(isbn)-1]
    code += str(calcCheckDigitForISBN10(code))
  return code

def isValidISBN10(code):
  result = False
  #isbn10 has 10 chars
  #first 9 chars should be number
  if re.match('^\d{9}[\d,X]{1}$', code):
    sum=0
    for i in range(0,9):
      sum += int(code[i]) * (i + 1)
      #print(sum, sum % 11)
    if code[9] == 'X':
      check_digit = 10
    else:
      check_digit = code[9]
    # sum += 10 if code[9] == 'X' else int(code[9]) * 10
    # result = sum % 11 == 0
  return sum % 11 == check_digit

def calcCheckDigitForISBN13(code):
  result = -1
  code = code.replace("-","")
  sum = 0
  for i in range(len(code)):
    digit = int(code[i])
    
    sum += digit * (3 if isOdd(i) else 1)
  
  result = (10 - sum % 10) % 10
  return result

def toISBN13(isbn):
  #converts isbn13 to isbn 10
  result = ""

  if isValidISBN10(isbn):
    isbn = isbn[:len(isbn)-1]
    result = "978" +isbn
    result += str(calcCheckDigitForISBN13(result))

  return result

def dld_kdata():

    agg = KeepaMAVG.objects.all()
 
    with open('kdata.csv', 'w') as f:
        writer = csv.writer(f)
        field_names = [field.name for field in agg.model._meta.fields] 
        writer.writerow(field_names)
        for obj in agg:
            writer.writerow([getattr(obj, field) for field in field_names])

def null_to_blank(item, n):
    if item : return item
    else : 
        if n in [0,2,3,4] : return ''
        elif n==1 : return date(2001,1,1)
        else : return 0

def str_date_to_sql(d):
    #returns datetime date as sql string date
    try:
        d = datetime.strptime(d, '%d/%m/%Y')
    except:
        try:
            d = datetime.strptime(d, '%d/%m/%y')
        except:
            try:
                d = datetime.strptime(d, '%d %b %y')
            except:
                try:
                    d = datetime.strptime(d, '%d%b%Y')
                except:
                    d = datetime.strptime(d, '%d.%m.%y')
    return f'{d.year}-{"{:02d}".format(d.month)}-{"{:02d}".format(d.day)}'

def numfix(z):
    if isinstance(z,float):
        return z
    elif isinstance(z,int):
        return z
    else:
        return re.sub('[^0-9.]', '', z)
      
def find_sleep_time(my_req,amt_left=0):
    #adjust sleep time to take account of remaining tokens
    tokens_left = my_req.json()['tokensLeft']
    sleep_time = 181
    if int(tokens_left) >= 50 : sleep_time = 120 
    if int(tokens_left) >= 100 : sleep_time = 30
    if int(tokens_left) >= 200 : sleep_time = 10
    if int(tokens_left) >= 1000 : sleep_time = 1
    print(f'you have {tokens_left} tokens left and sleep time is {sleep_time} and {amt_left} isbns remain')
    return sleep_time
  

def get_google_description(isbn):
  #gets google description and category from google book api
  base_url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
  full_url = base_url + isbn
  response = requests.get(full_url)
  data = json.loads(response.text)
  description = ''
  categories = []
  if "items" in data:  # if the book was found
            book_info = data["items"][0]  # take the first found book
            if "volumeInfo" in book_info and "categories" in book_info["volumeInfo"]:
                categories = book_info["volumeInfo"]["categories"]
            if "volumeInfo" in book_info and "description" in book_info["volumeInfo"]:
                description = book_info["volumeInfo"]["description"]

  return categories, description