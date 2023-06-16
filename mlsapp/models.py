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
