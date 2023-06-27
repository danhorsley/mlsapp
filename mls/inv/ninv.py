import csv
from mlsapp.models import WSInfo

def upload_ws_info_from_csv(file_path='mls/WSInfo.csv'):
    WSInfo.objects.all().delete()
    with open(file_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            ws_info = WSInfo(
                wholesaler=row['wholesaler'],
                params1=row['params1'],
                renames=row['renames'],
                style=row['style'],
                tab_num=int(row['tab_num']),
                discount=float(row['discount']),
                ccy=row['ccy'],
                terms=row['terms'],
                url=row['url']
            )
            ws_info.save()