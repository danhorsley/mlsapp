from mlsapp.models import Offers, static, WSInfo
import gc
import pandas as pd
from mls.offpop import check_or_create_static
from datetime import datetime
from django.utils import timezone
import pytz
    
    

#def bulk_load_data(file_path = 'mlsapp_keepajson5.csv',my_ws='boon', batch_size=300):
#def bulk_load_data(file_path = 'mlsapp_keepajson16.csv',my_ws='bestsellers', batch_size=300):
def bulk_load_data(file_path = 'mlsapp_keepajson8.csv',my_ws='66', batch_size=300):
    #with transaction.atomic():
        chunk_iterator = pd.read_csv(file_path, chunksize=batch_size)

        counter = 0
        #next_id = Offers.objects.last().id + 1 if Offers.objects.exists() else 1

        for chunk in chunk_iterator:
            objects=[]
            my_next_id = Offers.objects.order_by('-id').first().id
            for _, row in chunk.iterrows():
                counter+=1      
                #print(row)
                try:
                    d = datetime.strptime(row.date, '%Y-%m-%d 00:00:00')
                    my_book_id = check_or_create_static(row.book_id)
                    print(counter, d, my_book_id)
                    
                    obj,my_bool = Offers.objects.get_or_create( 
                                book = my_book_id, 
                                wholesaler = WSInfo.objects.filter(wholesaler=my_ws)[0],)
                    if  my_bool:  
                        obj.id =  my_next_id + counter    
                        obj.jf = row.jf
                        obj.date = timezone.datetime(d.year, d.month, d.day, tzinfo=pytz.UTC)
                        obj.is_live=True
                        objects.append(obj)
                    else:
                        pass
                except:
                    pass
                #counter += 1
                #next_id += 1
                #obj.save()

                # if counter >= batch_size:
            Offers.objects.bulk_create(objects)
            del objects[:]
            del chunk
            gc.collect()
            #counter = 0

        # Create any remaining objects that did not fill a complete batch
        if objects:
            Offers.objects.bulk_create(objects)
    
        
    