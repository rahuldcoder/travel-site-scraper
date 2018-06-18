import requests                
from bs4 import BeautifulSoup  
import csv                     
import webbrowser              



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

    # get number of reviews in all languages
    num_reviews = soup.find('span', class_='reviews_header_count').text 
    num_reviews = num_reviews[1:-1] 
    num_reviews = num_reviews.replace(',', '') 
    num_reviews = int(num_reviews) 
    print('[parse] num_reviews ALL:', num_reviews)

    url_template = url.replace('.html', '-or{}.html')
    
    # every subpages has 5 reviews
    
    items = []

    offset = 0

    while(True):
        subpage_url = url_template.format(offset)

        subpage_items = parse_reviews(session, subpage_url)
        if not subpage_items:
            break

        items += subpage_items
    
        if len(subpage_items) < 5:
            break

        offset += 5

    return items

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

        item = {
        
            'review_body': review.find('p', class_='partial_entry').text,
         
        }

        items.append(item)
    return items    

  
#----------------------------------------------------------------------
# CSV
#----------------------------------------------------------------------

def write_in_csv(items, filename='results.csv',
                  headers=['hotel name', 'review title', 'review body',
                           'review date', 'contributions', 'helpful vote',
                           'user name' , 'user location', 'rating'],
                  mode='w'):

    print('--- CSV ---')

    with open(filename, mode) as csvfile:
        csv_file = csv.DictWriter(csvfile, headers)

        if mode == 'w': # don't write headers if you append to existing file
            csv_file.writeheader()

        csv_file.writerows(items)


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

DB_HOST     = 'localhost'
DB_DATABASE = 'tripadvisor'
DB_PORT     = 3306
DB_TABLE    = 'reviews'
DB_COLUMN   = 'review_body'



# some URLs for testing
start_urls = [
    'https://www.tripadvisor.ca/Hotel_Review-g1480252-d316623-Reviews-Kuredu_Island_Resort_Spa-Kuredu.html',
    #'https://www.tripadvisor.com/Hotel_Review-g294229-d481832-Reviews-Pullman_Jakarta_Indonesia-Jakarta_Java.html',
    #'https://www.tripadvisor.com/Hotel_Review-g562819-d289642-Reviews-Hotel_Caserio-Playa_del_Ingles_Maspalomas_Gran_Canaria_Canary_Islands.html',
    #'https://www.tripadvisor.com/Hotel_Review-g60795-d102542-Reviews-Courtyard_Philadelphia_Airport-Philadelphia_Pennsylvania.html',
    #'https://www.tripadvisor.com/Hotel_Review-g60795-d122332-Reviews-The_Ritz_Carlton_Philadelphia-Philadelphia_Pennsylvania.html',
]

lang = 'in'

headers = [
 
    DB_COLUMN, #'review_body',
 
]
           
for url in start_urls:

    # get all reviews for 'url' and 'lang'
    items = scrape(url, lang)

    if not items:
        print('No reviews')
    else:
        # write in CSV
        filename = url.split('Reviews-')[1][:-5] + '__' + lang
        print('filename:', filename)
        write_in_csv(items, filename + '.csv', headers, mode='w')
        
        
