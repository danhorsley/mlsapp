from django.db import models

class static(models.Model):
    isbn13 = models.CharField(max_length=13, primary_key=True, unique=True)
    title = models.CharField(max_length=250)
    pubdate = models.DateField(default='2000-01-01')
    author = models.CharField(max_length=100)
    pubber = models.CharField(max_length=100)
    cover = models.CharField(max_length=30)
    height = models.FloatField(default=0)
    width = models.FloatField(default=0)
    thick = models.FloatField(default=0)
    weight = models.FloatField(default=0)
    rrp = models.FloatField(default=0)

class InvoiceData(models.Model):
    book = models.ForeignKey(static, on_delete=models.CASCADE,)
    quantity = models.IntegerField(default=0)
    title = models.CharField(max_length=200)
    cost = models.FloatField(default=1)
    totalprice = models.FloatField(default=1)
    date = models.DateField()
    inv_num = models.IntegerField(default=0)
    wholesaler = models.CharField(max_length=1)
    
class InvReader(models.Model):
    #params are inches in the order top,left, bottom right
    ws_name = models.CharField(max_length=25)
    invispdf = models.BooleanField(default=1)
    params1 = models.JSONField() 
    params2 = models.JSONField()
    params3 = models.JSONField()
    regex_num = models.CharField(max_length=50)
    regex_date = models.CharField(max_length=50)
    
class SalesData(models.Model):
    book = models.ForeignKey(static, on_delete=models.CASCADE,)
    date = models.DateTimeField()
    quantity = models.IntegerField(default=0)
    price = models.FloatField(default=1)
    post_crd = models.FloatField(default=0)
    salesfees = models.FloatField(default=0)
    postage = models.FloatField(default=0)
    wac = models.FloatField(default=1)
    profit = models.FloatField(default=1)
    
class SkuMap(models.Model):
    book = models.ForeignKey(static, on_delete=models.CASCADE,)
    sku = models.CharField(max_length=13)
    status = models.CharField(max_length=13, default = 'Active')
    
class KeepaJSONoffers(models.Model):
    #stores the query for a product on a particular day using ivnoice data as base
    #query includes buy box seller ID
    #this can later be accessed to populate TS models etc
    book = models.ForeignKey(static, on_delete=models.CASCADE,)
    jf = models.JSONField()
    date = models.DateTimeField()
    
class KeepaMAVG(models.Model):
    #monthly averages of relevant data for all products that have been in invoicedata
    book = models.ForeignKey(static, on_delete=models.CASCADE,)
    date = models.DateTimeField()
    new = models.FloatField(default=0)
    newfba = models.FloatField(default=0)
    newfbm = models.FloatField(default=0)
    salesrank = models.IntegerField(default=0)
    offerct = models.IntegerField(default=0)
    AZBBpct30 = models.FloatField(default=0)
    AZBBpct90 = models.FloatField(default=0)
    AZpx = models.FloatField(default=0)
    
class KeepaDataFXD(models.Model):
    #fixed data for all products that have been in invoicedata
    book = models.ForeignKey(static, on_delete=models.CASCADE,default='' )
    cat = models.JSONField(max_length=20, default=dict)
    pubdate = models.DateTimeField(default='2001-01-01')
    pap = models.JSONField(default=dict)
    h = models.IntegerField(default=0)
    l = models.IntegerField(default=0)
    w = models.IntegerField(default=0)
    wt = models.IntegerField(default=0)
    fmt = models.CharField(max_length=20, default='')
    
class WSInfo(models.Model):
    wholesaler = models.CharField(max_length=100, primary_key=True, unique=True)
    params1 = models.JSONField(default=dict)
    renames = models.JSONField(default=dict)  #renames invoice names to conform
    style = models.CharField(max_length=100)
    tab_num = models.IntegerField() #to see how many tables there are before main table
    csv_disc = models.FloatField(default=0.5) #discount to apply to initial stock csv price
    inv_disc = models.FloatField(default=0.5) #discount to apply to final invoice price
    ccy = models.CharField(max_length=10)
    terms = models.CharField(max_length=100)
    url = models.URLField(default=None)
    part_comb = models.BooleanField(default=False) #is this part of combined xl ws sheet
    csv_cols = models.JSONField(default=dict)  #renames csv offers names to conform
    
class Offers(models.Model):
    #populates offers past and present from all wholesalers
    #it has two foreign keys - the book and the wholesaler
    book = models.ForeignKey(static, on_delete=models.CASCADE,default='')
    wholesaler = models.ForeignKey(WSInfo, on_delete=models.CASCADE,default='')
    jf = models.JSONField(default=dict) #the json dictionary of the keepa data
    date = models.DateTimeField(default='2001-01-01') #last time updated
    is_live = models.BooleanField(default=True) #is this still a live offer
    
    class Meta:
        unique_together = ('book', 'wholesaler')  #this mean that we can have books offered by different supl but not vice v.
