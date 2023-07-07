from mlsapp.models import *
from mlsapp.utils import *
#from mls.ip import load_one_sr
from mlsapp.utils import null_to_blank
import csv

dodge = ['FS606', 'FS605', 'FS622',	'FS622', 'XDC349', 'IRIS020', 'IRIS035',
        'ARI022', 'NOTE039', 'NOTE050',	'NOTE056', 'NOTE056',	
        'NOTE001', 'CR047', 'A0-LPEX-6R6P',
        'B07CL5KHVJ',	'B07CS7CDVC',	'B07CS33NSZ',	'B07CS33NSZ',	'B07DKHV41T',	'B07M7PGLZX',	'B07M7PGLZX',	'XDC349',	'B078YYHW4Z',	
        'B094JNPG47',	'B07C53MWXM',	'B07N36YS16',	'B085LMMNXC',	'NOTE056',	'NOTE056',	'B079FPCSKS',	'B00OV3ZY76', 'B085TRDSD7','B085TRDSD7']

def create_dict():
    #create dictionary that maps isbn10s to an extant isbn13 in static model
    isbn13s = static.objects.values_list('isbn13', flat=True)
    my_dict = {}
    for item in isbn13s:
        if isValidISBN13(item):
            my_dict[toISBN10(item)] = item
    return my_dict

def isbn10_correct(my_isbn10):
    #fixes missing leading 0s at beginnign of isbn10
    ret = str(my_isbn10)
    n = len(ret)
    if n == 10 :
        return ret
    elif n < 10:
        ret = '0'* (10-n) + ret
        return ret
    else:
        return "isbn error"


def load_skus(reset=False):
    #loads skumap model using skumap csv.  sku csv map is created using colab notebook for now
    isbn_dict = create_dict()
    if reset:
        SkuMap.objects.all().delete() 
    with open("mls/sd/skumap.csv", "r") as f:
        reader = csv.reader(f)
        counter = -1
        for row in reader:
            counter += 1
            if counter ==0: pass
            else:
                if row[1] not in dodge:
                    
                    my_isbn10 = isbn10_correct(row[1])
                    print(row,my_isbn10)
                    try:
                        my_isbn13 = isbn_dict[my_isbn10]
                        book_link = static.objects.filter(isbn13 = my_isbn13)[0]
                        sm = SkuMap(book = book_link, sku = row[0], status = row[4])
                        sm.save()
                    except:
                        try:
                            my_isbn13 = toISBN13(my_isbn10)
                            print(f"loading isbn13 {my_isbn13} to static")
                            dims = find_dims(my_isbn13)
                            dims = [null_to_blank(dims[i],i) for i in range(len(dims))]
                            print(dims)
                            s = static(isbn13 = my_isbn13, title = dims[0][:200],
                                            pubdate = date_to_sql(dims[1]),
                                            author = dims[2], pubber = dims[3], cover = dims[4],
                                            height = dims[5], width = dims[6], thick = dims[7], weight = dims[8], rrp = 0)
                            s.save()
                            book_link = static.objects.filter(isbn13 = my_isbn13)[0]
                            sm = SkuMap(book = book_link, sku = row[0], status = row[4])
                            sm.save()
                        except:
                            print(f"could not load {my_isbn10}")
                else:
                    s = static(isbn13 = row[1], title = row[2],
                                            pubdate = '2001-01-01',
                                            author = 'nonbook', pubber = 'nonbook', cover = 'nonbook',
                                            height = 1 , width = 1, thick = 1, weight = 1, rrp = 0)
                    s.save()
                    book_link = static.objects.filter(isbn13 = row[1])[0]
                    sm = SkuMap(book = book_link, sku = row[0], status = row[4])
                    sm.save()