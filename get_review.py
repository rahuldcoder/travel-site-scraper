import requests                
from bs4 import BeautifulSoup  
import csv                     
import webbrowser              
import json
import os
import collections

def display(content, filename='output.html'):
    with open(filename, 'wb') as f:
        f.write(content)
        webbrowser.open(filename)


def get_soup(session, url, show=False):
    '''Read HTML from server and convert to Soup object'''

    # GET request and response with HTML
    r = session.get(url)

    # write html in file temp.html and open it in web browser.
    # see/test what we get from server.
    if show:
        display(r.content, 'temp.html')

    # check status code
    if r.status_code != 200: 
        print('[get_soup] status code:', r.status_code)
        # (as default) it will returns None instead of Soup
    else:
        return BeautifulSoup(r.text, 'html.parser')

#----------------------------------------------------------------------

def post_soup(session, url, params, show=False):
    
    # POST request and response with HTML
    r = session.post(url, data=params) # POST request

    if show:
        display(r.content, 'temp.html')


    if r.status_code != 200: 
        print('[post_soup] status code:', r.status_code)
     
    else:
        return BeautifulSoup(r.text, 'html.parser')

#----------------------------------------------------------------------

def scrape(url, lang='ALL'):

    # create session to keep all cookies (etc.) between requests
    session = requests.Session()

    session.headers.update({
        # some portals send correct HTML only if you have correct header 'user-agent'
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
    })

    items = parse(session, url)

    return items

#----------------------------------------------------------------------

def parse(session, url):
    '''Get number of reviews and start getting subpages with reviews'''

    soup = get_soup(session, url)

    if not soup:
        print('[parse] no soup:', url)
        return

    #Scraping the about section page

    hotel_amenities = soup.find_all('div',class_ ='hrAmenitiesSectionWrapper')
    
    
    textItem=[]

    for elements in hotel_amenities :
        item = elements.find_all('div',class_='textitem')
        textItem.append(item)

   

    if textItem:
        all_amenities = list()
        for item in textItem[0]:
            all_amenities.append(item.text)

        print(all_amenities)

   

     # Getting Traveller Ratings under category Excellent,Very Good,Average ,Poor, Terrible

    traveller_rating_dict = dict()

    count = soup.findAll('span',class_="is-shown-at-tablet")
    
    if count:
        traveller_rating_dict['Excellent'] = count[1].text
        traveller_rating_dict['Very good'] = count[3].text
        traveller_rating_dict['Average'] = count[5].text
        traveller_rating_dict['Poor'] = count[7].text
        traveller_rating_dict['Terrible'] = count[9].text

        print('Dictionary Printing')

        print('---------------------------')
        print(traveller_rating_dict)
        print('---------------------------')

    


    # get number of reviews in all languages
    num_reviews = soup.find('span', class_='reviews_header_count').text 
    num_reviews = num_reviews[1:-1] 
    num_reviews = num_reviews.replace(',', '') 
    num_reviews = int(num_reviews) 
    print('[parse] num_reviews ALL:', num_reviews)

    url_template = url.replace('.html', '-or{}.html')

    # get number of reviews in English language
    num_reviews = soup.select_one('div[data-value="en"] span').text # get text
    num_reviews = num_reviews[1:-1] # remove `( )`
    num_reviews = num_reviews.replace(',', '') # remove `,` in number (ie. 1,234)
    num_reviews = int(num_reviews) # convert text into integer
    print('[parse] num_reviews ENGLISH:', num_reviews)

    
    # every subpages has 5 reviews
    
    items = []

    offset = 0

    while(True):
        subpage_url = url_template.format(offset)

        subpage_items = parse_reviews(session, subpage_url)
        if not subpage_items:
            break

        items += subpage_items
    
        if len(subpage_items) < 5 :
            break

        offset += 5
    
    return items,traveller_rating_dict,all_amenities

#----------------------------------------------------------------------

def get_reviews_ids(soup):

    items = soup.find_all('div', attrs={'data-reviewid': True})

    if items:
        reviews_ids = [x.attrs['data-reviewid'] for x in items][::2]
        return reviews_ids

#----------------------------------------------------------------------

def get_more(session, reviews_ids):

    url = 'https://www.tripadvisor.com/OverlayWidgetAjax?Mode=EXPANDED_HOTEL_REVIEWS_RESP&metaReferer=Hotel_Review'

    payload = {
        'reviews': ','.join(reviews_ids), 
        'widgetChoice': 'EXPANDED_HOTEL_REVIEW_HSX', 
        'haveJses': 'earlyRequireDefine,amdearly,global_error,long_lived_global,apg-Hotel_Review,apg-Hotel_Review-in,bootstrap,desktop-rooms-guests-dust-en_US,responsive-calendar-templates-dust-en_US,taevents',
        'haveCsses': 'apg-Hotel_Review-in',
        'Action': 'install',
    }

    soup = post_soup(session, url, payload)

    return soup


#----------------------------------------------------------------------

def parse_reviews(session, url):
    '''Get all reviews from one page'''

    print('[parse_reviews] url:', url)

    soup =  get_soup(session, url)

    if not soup:
        print('[parse_reviews] no soup:', url)
        return

    hotel_name = soup.find('h1', id='HEADING').text

    reviews_ids = get_reviews_ids(soup)
    if not reviews_ids:
        return

    soup = get_more(session, reviews_ids)

    if not soup:
        print('[parse_reviews] no soup:', url)
        return

    items = []
    #reviewer_names = dict()

    
    # find all reviews on page
    #for idx, review in enumerate(soup.find_all('div', class_='review-container')): # reviews on normal page
    for idx, review in enumerate(soup.find_all('div', class_='reviewSelector')):  # reviews on page after click "More"

        # it has to check if `badgets` (contributions/helpful_vote) exist on page
        badgets = review.find_all('span', class_='badgetext')
        if len(badgets) > 0:
            contributions = badgets[0].text
        else:
            contributions = '0'

        if len(badgets) > 1:
            helpful_vote = badgets[1].text
        else:
            helpful_vote = '0'

        # check if `user_loc` exists on page
   
        user_loc = review.select_one('div.userLoc strong')
        if user_loc:
            user_loc = user_loc.text
        else:
            user_loc = ''

        bubble_rating = review.select_one('span.ui_bubble_rating')['class']
        bubble_rating = bubble_rating[1].split('_')[-1]

        item = dict()

        item = {
             'hotel name': hotel_name,

            'review title': review.find('span', class_='noQuotes').text,
            'review_body': review.find('p', class_='partial_entry').text,
            # 'ratingDate' instead of 'relativeDate'
            'review date': review.find('span', class_='ratingDate')['title'],

            'contributions': contributions,  # former 'num_reviews_reviewer'
            'helpful vote': helpful_vote,  # new

            # former 'reviewer_name'
            'user name': review.find('div', class_='info_text').find('div').text,
            'user location': user_loc,  # new
            'rating': bubble_rating,
         
        }

        items.append(item)

      
        for key,val in item.items():
            print(' ', key, ':', val)

    return items    

  
# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main(start_urls,directory):

    DB_COLUMN   = 'review_body'

    lang = 'in'

    headers = [
    
        DB_COLUMN, #'review_body',
    
    ]
            
    for url in start_urls:

        # get all reviews for 'url' and 'lang'
        items,traveller_rating_dict,all_amenities = scrape(url[1], lang)

        if not items:
            print('No reviews')
               
        else:
            
            if not os.path.exists(directory+'/'+str(url[0])):
                os.makedirs(directory+'/'+str(url[0]))
            filename = directory+'/'+str(url[0])+'/'+str(url[0])
            print('filename:', filename)

            with open(filename+'.json','w') as file_handler:
                for item in items:
                   json.dump(item,file_handler)
                   file_handler.write('\n\n\n\n\n')
     
            with open(filename+'_traveller_rating.json','w') as outfile:
                json.dump(traveller_rating_dict, outfile)     


            with open(filename+'_all_amenities.txt','w') as file_handler:
                for item in all_amenities:
                    file_handler.write(item+'\n')



if __name__ == '__main__':
    main(start_urls,directory)        
