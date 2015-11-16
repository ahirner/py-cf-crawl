import scrapy
#from bs4 import BeautifulSoup

import datetime
import requests

from pymongo import MongoClient, ReplaceOne

URL = "https://www.cofounderslab.com"
MONGOPORT = 27017 #3001
MISSING_ONLY = False

db = MongoClient('localhost', MONGOPORT).cf_crawl
profiles = db.cf_profiles
if MISSING_ONLY:
    p_cursor = profiles.find({'url' : {"$exists" : True}, 'detail_raw' : {'$exists' : False}})    
else:
    p_cursor = profiles.find({'url' : {"$exists" : True}})


#make life simple and do all in-memory
urls = [URL + p['url'] for p in p_cursor]
print "Total detail URLS: " + str(len(urls))

def write_results(p_url, detail_raw):
    data = {"$set" : {'detail_raw' : detail_raw, 'detail_retrieved' : datetime.datetime.utcnow()}}
    #requests = [ReplaceOne({'url': p_url}, data, upsert=True)]
    result = profiles.update_one({'url': p_url}, data, upsert=False)
    return result

class DetailSpider(scrapy.Spider):
    name = "cf-crawl-detail"
    start_urls = urls
    
    def parse(self, response):

        orig_url = response.url.replace(URL, "")
        if 'redirect_urls' in response.request.meta:
            print "REDIRECT!"
            red_url = response.meta['redirect_urls'][0].replace(URL, "")
            if (orig_url != red_url):
                print "Update url (%s) to url (%s)" % (orig_url, red_url)
                profiles.update_one({'url': red_url}, {"$set" : {'url' : orig_url}}, upsert=False)

        detail_body = response.xpath('//div[@class="newreg_wrap"]').extract()[0]
    
        w = write_results(orig_url, detail_body)
        print "modified %i entries from (%s)" % (w.modified_count, orig_url)    

        yield None
