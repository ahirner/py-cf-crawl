
# coding: utf-8

# In[116]:

from bs4 import BeautifulSoup

import datetime
import requests

from pymongo import MongoClient, ReplaceOne

URL = "https://www.cofounderslab.com"
SEARCH_URL = "https://www.cofounderslab.com/Index/postfilter'"
MONGOPORT = 27017 #3001


# In[117]:

def extract_summary(p):
    row = {}
    classes = ["profilebox_details_right","profilebox_details_basic"]
    #("div", class_ = "profilebox_details") ("div", class_ = "profilebox_details_basic")
    details = p.find("div", class_ = classes )
    #details += p.find("div", class_ = "profilebox_details_right_basic")
    
    if (details == None): 
        print "no following classes found: " + str(classes)
        print p
        return []
    
    #Details
    row['id'] = p['id'].replace("div_", '')
    row['_id'] = row['id'] #Try to replicate it to mongo unique key
    
    row['name'] = details.h2.text.strip()
    row['url'] = details.h2.a['href']
    position = details.find("span", class_="position_prof")
    if (position == None):
        position = details.find("span", class_="adviser_txt").text
    else: position = position.span.text
    row["position"]=position.strip()
    row['pro'] = (details.find("div", class_="pro_band") != None)
    row['loc'] = details.find("div", class_="prof_flag_country").text
    
    #Summary
    for item in p.find_all("div", class_="prof_text_summ"):
        field = item.find("div", class_="prof_text_summ_inner_1").text.strip().encode('ascii', 'ignore')
        desc = item.find("div", class_="prof_text_summ_inner_right_1").text.strip()
        row[field] = desc
        
    basic_items = p.find_all("div", class_="profilebox_details_right_basic")
    for item in basic_items:
        field = item.find("div", class_="prof_text_basic_inner").text.strip().encode('ascii', 'ignore')
        desc = item.find("div", class_="prof_text_basic_inner_right").text.strip()
        row[field] = desc       

    #timestamp
    row['summary_retrieved'] = datetime.datetime.utcnow()
        
    return row


# In[118]:

db = MongoClient('localhost', MONGOPORT).cf_crawl
profiles = db.cf_profiles
profiles.create_index("id", unique=True)


# In[129]:


def scrape_result_page(text):

    soup = BeautifulSoup(text)
    
    #find next url
    paginator = soup.find("div", class_="pagination")
    next_ = ""
    for link in paginator.find_all("a"):
        inner = link.text
        if "next" in inner.lower(): next_ = link['href']
    
    #attention: pro and basic profiles have different layout!
    profiles = soup.find_all("div", class_=["adv_profile_box", "basic_profile_box"])     
    if (len(profiles) < 20):
        print "only " + str(len(profiles)) + " profiles found"
    if (len(profiles) == 0):
        print conn.info()
        print conn.getcode()
        print soup.prettify()
    
    results = [extract_summary(p) for p in profiles]
    return results, next_
    
def write_results(collection, fetched):
    requests = [ReplaceOne({'id': p['id']}, p, upsert=True) for p in fetched]
    result = collection.bulk_write(requests)
    return result

def get_first(session, post_url, f):
    #f = '{"filter_submit":{"no_of_rec":20,"start_rec":0},"filter_delete":{"cities":["17585"]}}'
    values = {'filter_jsn' : f, 'archetype_submit' : 'Search', 'prst_prtnr_clg_flg' : '', 'prst_prtnr_aclrtr_flg' : ''}
    r = session.post(post_url, data=values)
    return r.text, r.url
    
def crawl_profiles(session, collection, filter_string, page = 0):
    print "Start Crawling Profiles on %s at page %s" % (URL, page)
    print "Interrupt anytime with KBD"
    
    try:
        #First retrieval
        text, url = get_first(session, SEARCH_URL, filter_string)   
        r, n_ = scrape_result_page(text)

        filter_boxes = BeautifulSoup(text).find_all("li", class_=["intentions_blue", "cities_blue", "roles_blue"])
        print "FILTERS: " + ", ".join([s.text.strip() for s in filter_boxes])
        
        if page == 0:
            n = n_
            w = write_results(collection, r)
            print "inserted/upserted %i, modified %i, deleted %i entries from (%s)" % (w.inserted_count + w.upserted_count, w.modified_count, w.deleted_count, url)
        else:
            n = '/page/' + str(page)
            url += n
        
        #Print filter settting
        
        while (url):
            #print "scraping.. " + URL + n
            page = session.get(url)
            text = page.text
            r, n = scrape_result_page(text)
            w = write_results(collection, r)
            
            print "inserted/upserted %i, modified %i, deleted %i entries from (%s)" % (w.inserted_count + w.upserted_count, w.modified_count, w.deleted_count, URL + n)    
            if len(r) > 0:
                if (n == ""): 
                    print "No more next page found on " + url + " | " + page.url
                    url = ""                    
                else: 
                    #hack for now.. no incremental links
                    url = URL + n
            else: url = ""
                
    except KeyboardInterrupt:
        print "Interrupted at URL %s" %url
        return n
    
    return n

f_all = '{"filter_submit":{"no_of_rec":20,"start_rec":0},"filter_delete":{"cities":["17585"]}}'
filters = [
    '{"filter_submit":{"no_of_rec":20,"start_rec":0, "intentions":["3"]},"filter_delete":{"cities":["17585"]}}',
    '{"filter_submit":{"no_of_rec":20,"start_rec":0, "intentions":["2"]},"filter_delete":{"intentions":["3"]}}',
    '{"filter_submit":{"no_of_rec":20,"start_rec":0, "intentions":["1"]},"filter_delete":{"intentions":["2"]}}'
    ]


s = requests.Session()
for f in filters:
    crawl_profiles(s, profiles, f, 0)
print "Total profiles now in collection: " + str(profiles.count())


