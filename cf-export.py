
# coding: utf-8

# In[1]:

import sys
from pymongo import MongoClient
import xlwt

MONGOPORT = 3001 #27017 #3001
OUT = "out"
if len(sys.argv) > 1: OUT = sys.argv[1]


# In[39]:

db = MongoClient('localhost', MONGOPORT).cf_crawl
profiles = db.cf_profiles

p_cursor = profiles.find({'detail_raw' : {"$exists" : True}})
print "Exporting %i profiles" % p_cursor.count()

def sheet_column(c):
    return c >> 8, (c & 255)

fields = None
with open('fields.txt') as fp:
    fields = [l.strip() for l in fp]

to_del = ['""', '_id', 'detail_raw']
essential = ["id", "url", "name", "loc" ,"I'm a", "position", "looking for a", 
             "to be my", "pro", "url", "video", "status", "about", "Industry", 
             "Industry Focus", "age", "fav", "last_act_days"]



#fields.sort()
essential.reverse()
for e in to_del:
    if e in fields: fields.pop(fields.index(e))
for es in essential:
    if es in fields: 
        fields.pop(fields.index(es))
        fields.insert(0, es)
         
    
nsheets = sheet_column(len(fields))[0] + 1
print "Total fields: %i, separated into %i sheets" %(len(fields), nsheets)

wb = xlwt.Workbook()
bold = xlwt.easyxf('font: bold 1')
sheets = [wb.add_sheet(str(i)) for i in range(nsheets)]
for i, f in enumerate(fields):
    s, c = sheet_column(i)
    sheets[s].write(0, c, f, bold)
    
#wb.save(OUT+".xls")


# In[40]:

i = 0
for p in p_cursor:
    try:
        if len(p) == 0: print "ERROR, retrieved 0 fields"
        for k,v in p.iteritems():
            if k in fields:
                print k,v 
                ind = fields.index(k)
                s, c = sheet_column(ind)
                sheets[s].write(i+1, c, v)
        if (i % 100): print "%i rows written" %i
        i += 1
    except KeyboardInterrupt:
        print "Interrupted .. last url: " + "http://www.cofounderslab.com"+p['url']
        break

wb.save(OUT+".xls")

