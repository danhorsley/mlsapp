import pandas as pd
import numpy as np
from datetime import date
from django.db.models import Sum, F
from mlsapp.models import InvoiceData, SalesData
from mlsapp.utils import date_to_sql

def ihist(my_date=date(2023, 6, 1)):
    # my_date is a datetime object
    # Convert my_date to an SQL-formatted date
    sql_date = date_to_sql(my_date)

    # Query the InvoiceData model and calculate invoice-related quantities
    invoice_query = InvoiceData.objects.filter(date__lte=sql_date).values('book_id', 'title').order_by('title') \
        .annotate(total_inv_qty=Sum(F('quantity'))) \
        .annotate(total_inv_cost=Sum(F('cost') * F('quantity'))) \
        .annotate(wavg_cost=(F('total_inv_cost') / F('total_inv_qty')))

    # Query the SalesData model and calculate sales-related quantities
    sales_query = SalesData.objects.filter(date__lte=sql_date).values('book_id').order_by('book_id') \
        .annotate(total_sales_qty=Sum(F('quantity')))

    # Convert the query results to DataFrames
    invoice_df = pd.DataFrame.from_dict(invoice_query)
    sales_df = pd.DataFrame.from_dict(sales_query)

    # Merge the invoice and sales DataFrames on 'book_id'
    merged_df = invoice_df.merge(sales_df, how='inner', right_on='book_id', left_on='book_id')

    # Read the damages data from an Excel file into a DataFrame
    damages_df = pd.read_excel('damages.xlsx')
    
    # Read the ebay_sales data from an Excel file into a DataFrame
    eb_df = pd.read_excel('ebay_sales.xlsx')
    eb_df['Sale date'] = pd.to_datetime(eb_df['Sale date']).dt.date
    eb_df = eb_df[eb_df['Sale date'] <= my_date]
    eb_df['ebay_qty']=  eb_df['Qty_mult']*eb_df['Quantity']
    eb_df = eb_df[['My code', 'ebay_qty']]
    eb_df.columns = ['isbn', 'ebay_qty']
    eb_agg=eb_df.groupby('isbn', as_index=False)['ebay_qty'].sum()

    # Convert the 'date' column to datetime objects and filter based on the provided date
    damages_df['date'] = pd.to_datetime(damages_df['date']).dt.date
    damages_df = damages_df[damages_df['date'] <= my_date]

    # Group the damages DataFrame by 'isbn' and count occurrences of 'price'
    damages_agg_df = damages_df.groupby('isbn', as_index=False)['price'].count()
    damages_agg_df.columns = ['isbn', 'damages']
    damages_agg_df['isbn'] = damages_agg_df['isbn'].astype(str)
    damages_agg_df['damages'] = damages_agg_df['damages'].astype(int)

    # Merge the main DataFrame with the damages DataFrame
    merged_df = merged_df.merge(damages_agg_df, how='left', left_on='book_id', right_on='isbn')
    merged_df = merged_df.merge(eb_agg, how='left', left_on='book_id', right_on='isbn')

    # Fill any missing values with 0
    merged_df = merged_df.fillna(0)

    # Calculate the stock quantity by subtracting sales and damages from total inventory
    merged_df['stock'] = merged_df['total_inv_qty'] - merged_df['total_sales_qty'] - merged_df['damages'] - merged_df['ebay_qty']

    # Select the desired columns
    final_df = merged_df[['book_id', 'title', 'total_inv_qty', 'total_sales_qty', 'damages', 'ebay_qty','stock', 'wavg_cost']]

    # Replace negative stock values with 0
    final_df['stock'] = np.where(final_df['stock'] < 0, 0, final_df['stock'])

    # Calculate stock value and damages value
    final_df['stock_val'] = final_df['stock'] * final_df['wavg_cost']
    final_df['dam_val'] = final_df['damages'] * final_df['wavg_cost']

    return final_df