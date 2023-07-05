from django.shortcuts import render
from .models import InvoiceData, SalesData, Static

def cheat_sheet(request):
    # Handle form submission
    if request.method == 'POST':
        title = request.POST.get('title')
        isbn = request.POST.get('isbn')
        wholesaler = request.POST.get('wholesaler')
        invoice_number = request.POST.get('invoice_number')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Query the database based on the filters
        filtered_data = Static.objects.filter(title__icontains=title, 
                                              isbn__icontains=isbn,
                                              wholesaler__icontains=wholesaler,
                                              invoice_data__invoice_number__icontains=invoice_number,
                                              invoice_data__date__range=[start_date, end_date])
        
        # Perform calculations on the filtered data
        total_units_bought = filtered_data.aggregate(total_units_bought=models.Sum('invoice_data__units'))
        total_units_sold = filtered_data.aggregate(total_units_sold=models.Sum('salesdata__units'))
        # Perform other calculations
        
        # Pass the data to the template
        context = {
            'filtered_data': filtered_data,
            'total_units_bought': total_units_bought['total_units_bought'],
            'total_units_sold': total_units_sold['total_units_sold'],
            # Add other calculated values to the context
        }
        return render(request, 'cheat_sheet.html', context)
    
    # Render the initial form
    return render(request, 'cheat_sheet.html')