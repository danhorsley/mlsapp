# Generated by Django 4.2.2 on 2023-06-16 11:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='static',
            fields=[
                ('isbn13', models.CharField(max_length=13, primary_key=True, serialize=False, unique=True)),
                ('title', models.CharField(max_length=250)),
                ('pubdate', models.DateField(default='2000-01-01')),
                ('author', models.CharField(max_length=100)),
                ('pubber', models.CharField(max_length=100)),
                ('cover', models.CharField(max_length=30)),
                ('height', models.FloatField(default=0)),
                ('width', models.FloatField(default=0)),
                ('thick', models.FloatField(default=0)),
                ('weight', models.FloatField(default=0)),
                ('rrp', models.FloatField(default=0)),
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
    ]
