import csv
from mlsapp.models import WSInfo
            
def upload_ws_info_from_csv(file_path='mls/WSInfo.csv'):
    with open(file_path, 'r', encoding="ISO-8859-1") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            ws_info, created = WSInfo.objects.get_or_create(wholesaler=row['wholesaler'])
            print(row)
            ws_info.params1 = row['params1']
            ws_info.renames = row['renames']
            ws_info.style = row['style']
            ws_info.tab_num = int(row['tab_num'])
            ws_info.csv_disc = float(row['csv_disc'])
            ws_info.inv_disc = float(row['inv_disc'])
            ws_info.ccy = row['ccy']
            ws_info.terms = row['terms']
            ws_info.url = row['url']
            ws_info.part_comb = row['part_comb']
            ws_info.csv_cols = row['csv_cols']
            ws_info.save()
            
