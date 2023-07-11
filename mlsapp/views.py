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
        
        #filtered_sales = SalesData.objects.filter(book_id=isbn)
        filtered_sales = SalesData.objects.filter(book_id=isbn,type='Order').exclude(order_id__in=SalesData.objects.filter(type='Refund').values('order_id'))
        filtered_adjustments = SalesData.objects.filter(book_id=isbn,type='Adjustment')
            
        
        # Perform calculations on the filtered data
        total_outlay =  invoice_agg[0].total_inv_cost
        total_units_bought = filtered_data.aggregate(total_units_bought=Sum('invoicedata__quantity'))
        total_units_sold = filtered_sales.aggregate(total_units_sold=Sum('quantity'))

        total_damaged = filtered_adjustments.aggregate(total_units_damaged=Sum('quantity'))
        total_dam_adj = filtered_adjustments.aggregate(total_dam_adj=Sum(F('price') * F('quantity')))['total_dam_adj']
        if total_dam_adj:
            pass
        else:
            total_damaged['total_units_damaged']=0
            total_dam_adj=0
        total_sales = filtered_sales.aggregate(total_sales=Sum(F('price') * F('quantity')))['total_sales']
        total_post_crd = filtered_sales.aggregate(total_pc=Sum('post_crd'))['total_pc']
        total_sales_fees = filtered_sales.aggregate(total_f=Sum('salesfees'))['total_f']
        total_post = filtered_sales.aggregate(total_post=Sum('postage'))['total_post']
        total_fees_all = total_post_crd + total_sales_fees + total_post
        avg_sales_price = total_sales /filtered_sales.aggregate(total_units_sold=Sum('quantity'))['total_units_sold']
        min_sale_px = (invoice_agg[0].wavg_cost - total_post/total_units_sold['total_units_sold'])
        if min_sale_px * 1.053 + 1< 5:
            min_sale_px = min_sale_px * 1.053 + 1
        else:
            min_sale_px = min_sale_px * 1.153 + 1
        # Perform other calculations
        
        # Pass the data to the template
        context = {
            'data' :{'title': filtered_data[0].title,
            'total_units_bought': total_units_bought['total_units_bought'],
            'total_units_sold': total_units_sold['total_units_sold'],
            'total_units_damaged': total_damaged['total_units_damaged'],
            'wavg_cost' : invoice_agg[0].wavg_cost,
            'total_outlay' : total_outlay,
            'total_sales' : total_sales,
            'total_post_crd' : total_post_crd,
            'total_sales_fees' : total_sales_fees,
            'total_post' : total_post,
            'total_fees_all' :total_fees_all,
            'actual_profit' : total_sales - total_outlay + total_fees_all + total_dam_adj,
            'trade_profit' : (total_sales - invoice_agg[0].wavg_cost*total_units_sold['total_units_sold']\
                                +total_dam_adj + total_fees_all),
            'avg_sales_price' : avg_sales_price,
            'profit_per_item' : (total_sales - invoice_agg[0].wavg_cost*total_units_sold['total_units_sold']\
                                + total_fees_all)/total_units_sold['total_units_sold'],
            'min_sale_px': min_sale_px,
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


def inv_search(request):
    if request.method == 'POST':
        search_type = request.POST.get('search_type')
        search_query = request.POST.get('search_query')
        
        if search_type == 'wholesaler':
            invoice_data = InvoiceData.objects.filter(wholesaler=search_query)
            
            # Calculate profit and loss per invoice number
            p_and_l = {}
            for invoice in invoice_data:
                sales_data = SalesData.objects.filter(inv_num=invoice.inv_num).order_by('date')
                inventory = {}
                total_profit = 0
                
                for sale in sales_data:
                    if sale.book_id not in inventory:
                        inventory[sale.book_id] = 0
                    
                    if inventory[sale.book_id] >= sale.quantity:
                        # Sufficient quantity in inventory, deduct from inventory and calculate profit
                        inventory[sale.book_id] -= sale.quantity
                        total_profit += sale.quantity * (sale.price - sale.wac)
                    else:
                        # Insufficient quantity in inventory, calculate profit using available quantity
                        available_quantity = inventory[sale.book_id]
                        inventory[sale.book_id] = 0
                        total_profit += available_quantity * (sale.price - sale.wac)
                
                p_and_l[invoice.inv_num] = total_profit
            
            context = {
                'invoice_data': invoice_data,
                'p_and_l': p_and_l
            }
            
            return render(request, 'inv_search.html', context)
        
        elif search_type == 'invoice_number':
            invoice_data = InvoiceData.objects.filter(inv_num=search_query)
            sales_data = SalesData.objects.filter(inv_num=search_query)
            
            context = {
                'invoice_data': invoice_data,
                'sales_data': sales_data
            }
            
            return render(request, 'inv_search.html', context)
    
    return render(request, 'inv_search.html')