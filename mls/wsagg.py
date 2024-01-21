from django.db.models import Sum, F, ExpressionWrapper, fields, Func, Value
from django.db.models.functions import Coalesce
from datetime import date, datetime, timedelta
from mlsapp.models import InvoiceData, SalesData

def calculate_fifo_returns(how = 'gross'):
    # Get all InvoiceData and SalesData records, ordered by date
    invoice_data = InvoiceData.objects.order_by('date')
    sales_data = SalesData.objects.order_by('date')

    # Initialize a dictionary to track the remaining quantity for each invoice
    invoice_quantity_remaining = {}

    # Initialize a dictionary to track returns for each invoice
    invoice_returns = {}

    for invoice in invoice_data:
        invoice_number = invoice.inv_num
        book_id = invoice.book_id
        quantity = invoice.quantity
        inv_date = invoice.date
        inv_cost = invoice.cost

        # Initialize or update the remaining quantity for the invoice
        invoice_quantity_remaining[(invoice_number, book_id, inv_date, inv_cost)] = quantity

    # Iterate through SalesData to calculate FIFO returns for each sale
    for sale in sales_data:
        try:
            sale_book_id = sale.book_id
            quantity_sold = sale.quantity
            selling_price = sale.price
            sales_fees = sale.salesfees
            sale_pcrds = sale.post_crd
            sale_post = sale.postage #+ sale.post_crd + sale.salesfees + sale.postage

            # Find the earliest invoice with remaining quantity for this book_id
            relevant_invoices = [(invoice_number,remaining_qty, inv_date,inv_cost) for \
                (invoice_number,book_id, inv_date,inv_cost), remaining_qty in \
                    invoice_quantity_remaining.items() if book_id == sale_book_id and remaining_qty > 0]
            

            if relevant_invoices:
                relevant_invoices.sort(key=lambda x: x[2])
                earliest_invoice = relevant_invoices[0]
                # Sort the relevant invoices by date and select the earliest one
                # Get the invoice number and remaining quantity
                invoice_number, remaining_quantity, inv_date, inv_cost = earliest_invoice
                #print(book_id, invoice_number, remaining_quantity, inv_date, inv_cost)
                # Calculate returns for the current sale
                if how == 'gross':
                    returns = min(quantity_sold, remaining_quantity) * (selling_price) + sales_fees + sale_pcrds + sale_post
                else:
                    returns = min(quantity_sold, remaining_quantity) * (selling_price - earliest_invoice[3]) + sales_fees + sale_pcrds + sale_post
                invoice_returns[invoice_number] = invoice_returns.get(invoice_number, 0) + returns

                # Update the remaining quantity for the invoice
                remaining_quantity -= min(quantity_sold, remaining_quantity)
                if remaining_quantity <= 0:
                    del invoice_quantity_remaining[(invoice_number, sale_book_id, inv_date, inv_cost)]
                    #print(f"Deleted {invoice_number} and book id {sale_book_id} from invoice_quantity_remaining")
                else:
                    #print(invoice_quantity_remaining[(invoice_number, sale_book_id, inv_date, inv_cost)], "**old**")
                    invoice_quantity_remaining[(invoice_number, sale_book_id, inv_date, inv_cost)] = remaining_quantity
                    #print(f"Updated {invoice_number} and book id {sale_book_id} in invoice_quantity_remaining")
                    #print(invoice_quantity_remaining[(invoice_number, sale_book_id, inv_date, inv_cost)], "**new**")

        # Now, 'invoice_returns' dictionary contains the FIFO returns for each invoice
        except:
            print("Error")
            pass
        
    return invoice_returns, invoice_quantity_remaining


def w_date_in():
    #calculate avg weighted date in by supplier
    ret_dict = {}
    suppliers = InvoiceData.objects.values('wholesaler').distinct()

    for supplier in suppliers:
        wholesaler_id = supplier['wholesaler']
        total_spent = InvoiceData.objects.filter(wholesaler=wholesaler_id).aggregate(Sum('totalprice'))['totalprice__sum']

        # Calculate the weighted average date of capital on the way in
        w_avg_date = InvoiceData.objects.filter(wholesaler=wholesaler_id)\
                                        .annotate(year=F('date__year'), month=F('date__month'), day=F('date__day')) \
                                        .annotate(numeric_date=ExpressionWrapper(
                                        (F('year') -2000 )* 365 + F('month') * 30 + F('day'),  # Convert to numeric date format
                                        output_field=fields.IntegerField())) \
                                        .annotate(w_date = (F('numeric_date') * F('totalprice'))/total_spent)\
                                        .aggregate(wavg_date=Sum('w_date'))['wavg_date']
        ret_dict[wholesaler_id] = [timedelta(w_avg_date) + date(2000,1,1), total_spent]
    return ret_dict

def total_ret_by_supplier():
    #calculate total returns by supplier
    ret_dict = {}
    suppliers = InvoiceData.objects.values('wholesaler').distinct()
    all_inv_returns = calculate_fifo_returns()[0]
    for supplier in suppliers:
        supplier_inv_nums = [x['inv_num'] for x in InvoiceData.objects.filter(wholesaler=supplier['wholesaler']).values('inv_num').distinct()]
        for inv_num in all_inv_returns:
            if inv_num in supplier_inv_nums:
                ret_dict[supplier['wholesaler']] = ret_dict.get(supplier['wholesaler'], 0) + all_inv_returns[inv_num]
                
    return ret_dict

def stats_by_supplier():
    ret_dict={}
    returns = total_ret_by_supplier()
    purchases = w_date_in()
    for supplier in returns:
        p =  purchases[supplier][1]
        s = returns[supplier]
        d = purchases[supplier][0]
        days = (date.today() - d).days
        roc = ((s-p)/p) * 365/days
        str_pct_rtn =  "{:.2%}".format((s-p)/p)
        ret_dict[supplier] = ["{:.2f}".format(purchases[supplier][1]),
                              "{:.2f}".format(returns[supplier]),
                                str_pct_rtn, days, 
                                "{:.2%}".format(roc)]
    return ret_dict


