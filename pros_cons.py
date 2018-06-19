import requests
from bs4 import BeautifulSoup
import pprint

def parser(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text,'html.parser')

    section_pros = soup.find('section',{'class' : 'pros'}).ul.contents
    section_cons = soup.find('section',{'class' : 'cons'}).ul.contents

    new_line_char = '\n'

    section_pros = list ( filter (lambda item: item != new_line_char, section_pros ) )
    section_cons = list ( filter (lambda item : item != new_line_char ,section_cons ) )


    file_name = url[39:]

    with open(file_name+'-PROS.txt','w') as file_handle:
        
        file_handle.write('PROS'+'\n')
        for html_item in section_pros:
            file_handle.writelines(html_item.text+'\n')

    with open(file_name+'-CONS.txt','w') as file_handle:

        file_handle.write('CONS'+'\n')
        for html_item in section_cons:
            file_handle.writelines(html_item.text+'\n')


# Enter the url for the Oyester website
def main(urls):
    pp = pprint.PrettyPrinter(indent=4)
  
    for url in urls:
        parser(url)

if __name__ == '__main__':
    main(urls)   
