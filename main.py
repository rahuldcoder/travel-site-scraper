import os
import pandas as pd 
from pandas.parser import CParserError
import get_review
import pros_cons


filename = input('Enter the csv file'+'\n')


#reading csv file
try :
    df = pd.read_csv(filename)
 #   print(df.head())
except CParserError:
    print(filename, 'failed: check for header rows')

# getting header names
headers = df.columns.values

for directory in headers :
    if not os.path.exists(directory):
        os.makedirs(directory)

# dictionary of query items
query_dict = dict.fromkeys(headers)


for directory in headers:
    all_urls = df[directory]
  #  print(all_urls.tolist() )
    trip_advisor_urls = list()
    trip_advisor_urls_no = list()
    count = 0
    for url in all_urls:
        if (url.startswith('https://www.tripadvisor') ): 
            trip_advisor_urls.append(url)
            trip_advisor_urls_no.append(count)
        count = count + 1  

    trip_advisor_data = zip(trip_advisor_urls_no,trip_advisor_urls)    
    get_review.main(trip_advisor_data,directory)

    oyester_urls = list()
    oyester_urls_no = list()
    count = 0
    for url in all_urls:
        if ( url.startswith('https://www.oyster') ) :
            oyester_urls.append(url)
            oyester_urls_no.append(count)
        count = count + 1    
    oyester_data = zip(oyester_urls_no,oyester_urls)    
  
    pros_cons.main(oyester_data,directory)        
