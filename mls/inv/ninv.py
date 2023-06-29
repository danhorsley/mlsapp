import csv
from mlsapp.models import WSInfo

def upload_ws_info_from_csv(file_path='mls/WSInfo.csv'):
    WSInfo.objects.all().delete()
    with open(file_path, 'r', encoding = "ISO-8859-1") as csv_file:
        reader = csv.DictReader(csv_file, )
        for row in reader:
            #print(row['renames'])
            ws_info = WSInfo(
                wholesaler=row['wholesaler'],
                params1=row['params1'],
                renames=row['renames'],
                style=row['style'],
                tab_num=int(row['tab_num']),
                csv_disc=float(row['csv_disc']),
                inv_disc=float(row['inv_disc']),
                ccy=row['ccy'],
                terms=row['terms'],
                url=row['url'],
                part_comb=row['part_comb']
            )
            ws_info.save()
            
