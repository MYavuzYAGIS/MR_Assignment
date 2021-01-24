from bs4 import BeautifulSoup as tarhana
import requests
import csv
import concurrent.futures
import re

custom_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36","Upgrade-Insecure-Requests": "1" ,"sec-fetch-mode": "navigate", 'Connection':'close'}


companies=[]
connected=[]
favicon_url=[]
logo_url=[]
not_connected=[]

#read urls from file and load into list
def load_companies(file):
    print('reading list and loading into memory')
    with open(file,'r') as file:
        list = csv.reader(file)
        for row in list:
            company = 'http://'+','.join(row)
            companies.append(company)

#filtering the list based on response status. sometimes we have 4XX or 5XX responses due to cookie overriding problem.
def isConnected(item):
    try:
        result = requests.get(item, headers=custom_headers,timeout=2)
        if len(result.text) > 0 and result.ok:
            connected.append(item)
        else:
            not_connected.append(item)
    except (requests.ConnectTimeout, requests.HTTPError, requests.ReadTimeout, requests.Timeout, requests.ConnectionError):
        not_connected.append(item)    

#fetching favicons
def fetch_favicon(item):
    #testing for best practices first, which is xyz.com/favicon.ico
    best_practice_url = item + '/favicon.ico'
    response_possible = requests.get(best_practice_url,headers=custom_headers,verify=True, timeout=2)
    try:
        if response_possible.ok:
            found = best_practice_url
            favicon_url.append(found)
        else:
            response = requests.get(item, headers=custom_headers, verify=True,timeout=2)
            soup = tarhana(response.content, features='lxml')
            # Looking for a direct url hit first.
            icon = soup.find('link', rel='icon')
            if icon and icon.has_attr('href'):
                found= icon['href']
                # there are couple of possible ways the url is given. absolute? relative? protocol-relative?
                #A) protocol-relative
                if found.startswith('//'):
                    found = found.split('//')[1]
                    found = item + '/' + found
                    favicon_url.append(found)            
                #B) absolute path    
                elif found.startswith('/'):
                    found = item + found    
                    favicon_url.append(found)
                else:
                    favicon_url.append(found)
            else:
                found = item + 'Not Found'
                favicon_url.append(found)
    except (requests.ConnectTimeout, requests.HTTPError, requests.ReadTimeout, requests.Timeout, requests.ConnectionError):
            found = item + 'Raised Exception'
            favicon_url.append(found)


def get_logo_url(item):
    response = requests.get(item, headers=custom_headers, verify=True,timeout=2)
    barebones= item.split('http://')[1].split('.')[0].capitalize()
    try:
        if len(response.text) > 0 and response.ok:
            soup = tarhana(response.content, features='lxml')
            image2=soup.find('img',src=re.compile('logo|svg|png|%s' %barebones))
            image=soup.find('meta', property='og:image')
            if image:
                found=item + '   ,    '+ image['content']
                logo_url.append(found)
            # searching image in the body of html.
            elif image2:
                found=item + '   ,    '+ image['src']
                logo_url.append(found)
            else:
                found = item + '   ,    '+ '  INLINE SVG || HARDCODED STRING || CSS Backgorund'
                logo_url.append(found)
        else:
            found = item + '   ,    '+ 'NO LOGO FOUND'
            logo_url.append(found)
    except (requests.ConnectTimeout, requests.HTTPError, requests.ReadTimeout, requests.Timeout, requests.ConnectionError):
        found = 'NO LOGO FOUND'
        logo_url.append(found)
        

def main():
    load_companies('websites.csv')
    # 1600% faster than a loop.
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        for item in companies:
            executor.submit(isConnected,item=item)
     # getting logos urls       
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        for item in connected:
            executor.submit(get_logo_url,item=item)
    # getting favicon urls
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        for item in connected:
            executor.submit(fetch_favicon,item=item)

    #Writing findings on output.csv file
    with open('output.csv', 'wt') as file:
        writer =csv.writer(file)
        writer.writerow(['Company','logo'])
        for row in logo_url:
            writer.writerow([row])   
    
    with open('not_connected.csv', 'wt') as file:
        writer =csv.writer(file)
        writer.writerow(['Company'])
        for row in not_connected:
            writer.writerow([row]) 
    with open('favicon.csv', 'wt') as file:
        writer =csv.writer(file)
        writer.writerow(['Company','favicon'])
        for row in favicon_url:
            writer.writerow([row]) 
    # #Stats         
    print('there was ' + str(len(companies)) + ' items in the list ' +  str(len(connected)) +  '  connected '  + ' and ' + str(len(not_connected)) + ' not connected')
    print('loss of overall url list is ' + str((len(companies)-len(connected))/ len(companies) * 100) + '%')
    print( 'number of logos found:  '+str(len(logo_url)))
    print( 'found favicons: ' +   str(len(favicon_url))) 



if __name__ == '__main__':
    main()