# travel-site-scraper
program to scrape trip advisor and oyester website
   else:
      
            filename = url.split('Reviews-')[1][:-5] + '__' + lang
            print('filename:', filename)
            with open(filename+'.txt','w') as file_handler:
                file_handler.writelines(items)

        '''