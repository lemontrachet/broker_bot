import socks
import socket
import requests
from BeautifulSoup import BeautifulSoup as bs
import mechanize
import os
import optparse
import re
import urllib, urllib2
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from anonBrowser import *

socks.setdefaultproxy(proxy_type=socks.PROXY_TYPE_SOCKS5, addr="127.0.0.1", port=9050)
socket.socket = socks.socksocket
print "ip:"
print requests.get("http://icanhazip.com").text

def testUserAgent(url, userAgent):
    browser = mechanize.Browser()
    browser.addheaders = userAgent
    page = browser.open(url)
    source_code = page.read()
    print source_code

def printCookies(url):
    browser = mechanize.Browser()
    cookie_jar = cookielib.LWPCookieJar()
    browser.set_cookiejar(cookie_jar)
    page = browser.open(url)
    for cookie in cookie_jar:
        print cookie

def printLinks(url):
    ab = anonBrowser()
    ab.anonymize()
    page = ab.open(url)
    html = page.read()
    
    try:
        print '\n[+] Printing links from BeautifulSoup.'
        soup = bs(html)
        print soup
        links = soup.findAll(name = 'a')
        for link in links:
            print "as"
            if link.has_key('href'):
                print link['href']
    except:
        pass

def mirrorImages(url, dir):
    ab = anonBrowser()
    ab.anonymize()
    html = ab.open(url)
    soup = bs(html)
    image_tags = soup.findAll('img')
    for image in image_tags:
        filename = image['src'].lstrip('http://')
        filename = os.path.join(dir,\
                                filename.replace('/', '_'))
        print '[+] Saving ' + str(filename)
        try:
            data = ab.open(image['src']).read()
            ab.back()
            save = open(filename, 'wb')
            save.write(data)
            save.close()
        except:
            pass

def image_data(img):
    image = Image.open(img)
    print(image)
    info = image._getexif()
    print(info)
    keys = [(TAGS.get(tag, tag), str(value)) for tag, value
                                            in info.items()]
    print(keys)


# ip and browser check
url = 'http://ipmonkey.com/'
userAgent = [('User-agent', 'Mozilla/5.0 (X11; U; '+\
              'Linux 2.4.2-2 i586; en-US; m18) Gecko/20010131 Netscape6/6.01')]

testUserAgent(url, userAgent)
#mirrorImages('http://news.bbc.co.uk', '/tmp/')
image_data('/home/pi/cars.jpeg')
