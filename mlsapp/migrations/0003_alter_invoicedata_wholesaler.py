# Generated by Django 4.2.2 on 2023-07-12 11:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mlsapp', '0002_alter_offers_wholesaler'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoicedata',
            name='wholesaler',
            field=models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.SET_NULL, to='mlsapp.wsinfo'),
        ),
    ]
