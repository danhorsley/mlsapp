# Generated by Django 4.2.2 on 2023-07-06 12:50

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InvReader',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ws_name', models.CharField(max_length=25)),
                ('invispdf', models.BooleanField(default=1)),
                ('params1', models.JSONField()),
                ('params2', models.JSONField()),
                ('params3', models.JSONField()),
                ('regex_num', models.CharField(max_length=50)),
                ('regex_date', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='static',
            fields=[
                ('isbn13', models.CharField(max_length=13, primary_key=True, serialize=False, unique=True)),
                ('title', models.CharField(max_length=250)),
                ('pubdate', models.DateField(default=datetime.datetime(2001, 1, 1, 0, 0, tzinfo=datetime.timezone.utc))),
                ('author', models.CharField(max_length=100)),
                ('pubber', models.CharField(max_length=100)),
                ('cover', models.CharField(max_length=30)),
                ('height', models.FloatField(default=0)),
                ('width', models.FloatField(default=0)),
                ('thick', models.FloatField(default=0)),
                ('weight', models.FloatField(default=0)),
                ('rrp', models.FloatField(default=0)),
                ('category', models.CharField(default='', max_length=50)),
                ('description', models.CharField(default='', max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='WSInfo',
            fields=[
                ('wholesaler', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True)),
                ('params1', models.JSONField(default=dict)),
                ('renames', models.JSONField(default=dict)),
                ('style', models.CharField(max_length=100)),
                ('tab_num', models.IntegerField()),
                ('csv_disc', models.FloatField(default=0.5)),
                ('inv_disc', models.FloatField(default=0.5)),
                ('ccy', models.CharField(max_length=10)),
                ('terms', models.CharField(max_length=100)),
                ('url', models.URLField(default=None)),
                ('part_comb', models.BooleanField(default=False)),
                ('csv_cols', models.JSONField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SkuMap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(max_length=13)),
                ('status', models.CharField(default='Active', max_length=13)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mlsapp.static')),
            ],
        ),
        migrations.CreateModel(
            name='SalesData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('quantity', models.IntegerField(default=0)),
                ('price', models.FloatField(default=1)),
                ('post_crd', models.FloatField(default=0)),
                ('salesfees', models.FloatField(default=0)),
                ('postage', models.FloatField(default=0)),
                ('wac', models.FloatField(default=1)),
                ('profit', models.FloatField(default=1)),
                ('type', models.CharField(default='Order', max_length=25)),
                ('order_id', models.CharField(default='Order', max_length=25)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mlsapp.static')),
            ],
        ),
        migrations.CreateModel(
            name='KeepaMAVG',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('new', models.FloatField(default=0)),
                ('newfba', models.FloatField(default=0)),
                ('newfbm', models.FloatField(default=0)),
                ('salesrank', models.IntegerField(default=0)),
                ('offerct', models.IntegerField(default=0)),
                ('AZBBpct30', models.FloatField(default=0)),
                ('AZBBpct90', models.FloatField(default=0)),
                ('AZpx', models.FloatField(default=0)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mlsapp.static')),
            ],
        ),
        migrations.CreateModel(
            name='KeepaJSONoffers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jf', models.JSONField()),
                ('date', models.DateTimeField()),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mlsapp.static')),
            ],
        ),
        migrations.CreateModel(
            name='KeepaDataFXD',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cat', models.JSONField(default=dict, max_length=20)),
                ('pubdate', models.DateTimeField(default=datetime.datetime(2001, 1, 1, 0, 0, tzinfo=datetime.timezone.utc))),
                ('pap', models.JSONField(default=dict)),
                ('h', models.IntegerField(default=0)),
                ('l', models.IntegerField(default=0)),
                ('w', models.IntegerField(default=0)),
                ('wt', models.IntegerField(default=0)),
                ('fmt', models.CharField(default='', max_length=20)),
                ('book', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='mlsapp.static')),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=0)),
                ('title', models.CharField(max_length=200)),
                ('cost', models.FloatField(default=1)),
                ('totalprice', models.FloatField(default=1)),
                ('date', models.DateField()),
                ('inv_num', models.IntegerField(default=0)),
                ('wholesaler', models.CharField(max_length=1)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mlsapp.static')),
            ],
        ),
        migrations.CreateModel(
            name='Offers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jf', models.JSONField(default=dict)),
                ('date', models.DateTimeField(default=datetime.datetime(2001, 1, 1, 0, 0, tzinfo=datetime.timezone.utc))),
                ('is_live', models.BooleanField(default=True)),
                ('book', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='mlsapp.static')),
                ('wholesaler', models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='mlsapp.wsinfo')),
            ],
            options={
                'unique_together': {('book', 'wholesaler')},
            },
        ),
    ]
