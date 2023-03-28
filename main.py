import requests
import sys

from bs4 import BeautifulSoup, SoupStrainer
from urllib.request import Request, urlopen
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from flask import escape
import functions_framework
from google.cloud import storage


username = 'jeremy@servant7.com' #config['username']
password = 'tester123' #config['password']
BUCKET_NAME = 'test'

headers = {
    'Host': 'rfpalooza.com',
    'Origin': 'https://rfpalooza.com',
    'Authority': 'rfpalooza.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
    'Referer': 'https://www.rfpalooza.com',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}

def list_files():
    storage_client = storage.Client()
    try:
        bucket = storage_client.create_bucket(BUCKET_NAME)
    except Exception as e:
        pass
    blobs = storage_client.list_blobs(BUCKET_NAME)
    return [ x.name for x in blobs ]
  

def extract(tag):
    try:
        return (tag['name'], tag['value'])
    except:
        return {}

def save_pdf(pdf_link, existing):
    filename = pdf_link.split('/')[-1]
    if filename not in existing:
        print (f'requesting pdf: {pdf_link}')
        req = Request(url=pdf_link, headers={'User-Agent': 'Mozilla/5.0'})
        r = urlopen(req).read()
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        with blob.open('w') as f:
            f.write(r)
        return filename

@functions_framework.http
def rfp_robot1(req):
    new_files = []
    with requests.Session() as s:

        # Login here
        s.headers.update(headers)
        resp = s.get('https://rfpalooza.com/login')
        soup = BeautifulSoup(resp.content, 'html.parser')
        payload = dict(extract(x) for x in soup.find_all('input', type='hidden') if extract(x))
        payload.update(
            {
                'pmpro_login_from_used' : '1',
                'wp-submit' : 'Log In',
                'log' : username,
                'pwd' : password,
                'redirect_to' : '',
            }
        )

        resp = s.post('https://rfpalooza.com/wp-login.php?wpe-login=true', data=payload)
        print (resp)
        print ("Completed logging in... ")

        cookies = resp.cookies
    
        if resp.status_code in [ 200, 302 ]:
          # Navigate to the Inventory page
          print ('navigating to the actual page')
          resp = s.get('https://rfpalooza.com/latest-advertising-marketing-rfps-2/')
          print (resp)
          msoup = BeautifulSoup(resp.content, 'html.parser')
          pdf_links = [ x['href'] for x in msoup.find_all('a') if x['href'].endswith('.pdf') ]
          #[ save_pdf(x) for x in pdf_links ]

          existing = list_files()
          new_file = save_pdf(pdf_links[0], existing)
          if new_file:
              new_files.append(new_file)

    return new_files
      
