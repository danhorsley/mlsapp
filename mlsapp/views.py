from django.shortcuts import render
from .models import InvoiceData, SalesData, static
from django.db.models import Sum, F

def cheat_sheet(request):
    
    first_invoice_date = InvoiceData.objects.order_by('date').values('date').first()['date'].strftime('%Y-%m-%d')
    last_invoice_date = SalesData.objects.order_by('-date').values('date').first()['date'].strftime('%Y-%m-%d')
    # Handle form submission
    if request.method == 'POST':
        title = request.POST.get('title')
        isbn = request.POST.get('isbn')
        wholesaler = request.POST.get('wholesaler')
        invoice_number = request.POST.get('invoice_number')
        start_date = request.POST.get('start_date', first_invoice_date)
        end_date = request.POST.get('end_date', last_invoice_date)
        
        # Query the database based on the filters
        filtered_data = static.objects.filter(title__icontains=title, 
                                              isbn13__icontains=isbn, #maybe should be __exact
                                              invoicedata__wholesaler__icontains=wholesaler,
                                              invoicedata__inv_num__icontains=invoice_number,
                                              invoicedata__date__range=[start_date, end_date]
                                              )
        
        invoice_agg = filtered_data.annotate(total_inv_cost=Sum(F('invoicedata__cost')*F('invoicedata__quantity')))\
                                    .annotate(total_inv_qty=Sum(F('invoicedata__quantity')))\
                                    .annotate(wavg_cost = (F('total_inv_cost')/F('total_inv_qty')))
        
        filtered_sales = SalesData.objects.filter(book_id=isbn)
        
        # Perform calculations on the filtered data
        total_outlay =  invoice_agg[0].total_inv_cost
        total_units_bought = filtered_data.aggregate(total_units_bought=Sum('invoicedata__quantity'))
        total_units_sold = filtered_sales.aggregate(total_units_sold=Sum('quantity'))
        total_sales = filtered_sales.aggregate(total_sales=Sum(F('price') * F('quantity')))['total_sales']
        total_post_crd = filtered_sales.aggregate(total_pc=Sum('post_crd'))['total_pc']
        total_sales_fees = filtered_sales.aggregate(total_f=Sum('salesfees'))['total_f']
        total_post = filtered_sales.aggregate(total_post=Sum('postage'))['total_post']
        total_fees_all = total_post_crd + total_sales_fees + total_post
        avg_sales_price = total_sales /filtered_sales.aggregate(total_units_sold=Sum('quantity'))['total_units_sold']
        
        # Perform other calculations
        
        # Pass the data to the template
        context = {
            'data' :{'title': filtered_data[0].title,
            'total_units_bought': total_units_bought['total_units_bought'],
            'total_units_sold': total_units_sold['total_units_sold'],
            'wavg_cost' : invoice_agg[0].wavg_cost,
            'total_outlay' : total_outlay,
            'total_sales' : total_sales,
            'total_post_crd' : total_post_crd,
            'total_sales_fees' : total_sales_fees,
            'total_post' : total_post,
            'total_fees_all' :total_fees_all,
            'actual_profit' : total_sales - total_outlay + total_fees_all,
            'avg_sales_price' : avg_sales_price,
            'profit_per_item' : (total_sales - total_outlay + total_fees_all)/total_units_sold['total_units_sold']
            #wholesalers
            #inventory remaining
            #roic
        }
        }
        for k in context :
            print(k)  # Check the value of filtered_data
        
        return render(request, 'cheat_sheet.html', context)
    
    default_context = {
                        'default_isbn' :  '9781405370134',  #Let's get talking
                        'start_date': first_invoice_date,
                        'end_date': last_invoice_date,
                        }
    # Render the initial form
    return render(request, 'cheat_sheet.html', default_context)