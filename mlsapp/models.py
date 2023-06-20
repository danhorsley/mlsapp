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
