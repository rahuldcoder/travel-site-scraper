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

# getting query for each folders

for directory in headers :
    queries = list()
    print('Enter the space separated queries for '+directory)
    queries = input().split()
    query_dict[directory] = queries

for directory in headers:
    all_urls = df[directory]
  #  print(all_urls.tolist() )
    trip_advisor_urls = list()
    for url in all_urls:
        if (url.startswith('https://www.tripadvisor') ): 
            trip_advisor_urls.append(url)
          
   # get_review.main(trip_advisor_urls)

    oyester_urls = list()
    for url in all_urls:
        if ( url.startswith('https://www.oyster.com') ) :
            oyester_urls.append(url)
    pros_cons.main(oyester_urls)        
