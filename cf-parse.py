
import sys
from pymongo import MongoClient
from bs4 import BeautifulSoup, element
import pandas as pd

MONGOPORT = 27017 #3001
OUT = "out"
if len(sys.argv) > 1: OUT = sys.argv[1]
LIMIT = 999

# In[2]:

class DictData(dict):
    def insert(self, d, postprocess = None):
        if d is None: return
        for k,v in d.iteritems():
            if v is not None:
                res = v
                
                if type(res) is list or type(res) is element.ResultSet:
                    res = [r for r in res if not None]
                    for i, r in enumerate(res): 
                        self.insert({k+'_'+str(i) : r}, postprocess)
                    return
                
                #todo: integize
                if postprocess is not None:
                    res = postprocess(res)
                    #print k, type(res), res
                    
                if type(res) is element.Tag: 
                    res = res.get_text(strip = True)
                elif res is str or v is unicode: res = res.strip()
             
                self[k] = res

def parse_detail(soup):
    data = DictData()
    sec = soup.find("div", class_ = ["basic_dtl", "founder_head"])
    #print type(sec.find("span", class_ = "cir_today_txt_new"))
    #print sec.find("span", class_ = "cir_today_txt_new").get_text()

    if sec is not None:
        data.insert({'fav': sec.find("span", class_ = "cir_innertext_new")})

        resp = sec.find("div", class_ = "r2_new")
        if resp is not None:
            data.insert({'responsiveness': resp.img}, lambda i: i['src'].split('/')[-1][:-4])

        data.insert({'last_act_days': sec.find("span", class_ = "cir_today_txt_new")}, lambda t: 0 if t.get_text(strip=True).lower() == "today" else t)

    sec = soup.find("div", class_ = "profile_status")
    if sec is not None:
        data.insert({'status' : sec.find("span","status_text")}, lambda s: s.b)

    sec = soup.find("div", class_ = "other_advising")
    if sec is not None:
        data.insert({'interest' : sec.findAll("span", class_="single")})

    sec = soup.find("div", class_ = "section_box about")
    if sec is not None:
        data.insert({'about' : sec.find("div", class_="show")}, lambda t: unicode(t.get_text()))


    sec = soup.find("div", class_ = "section_box skills")
    if sec is not None:
        left = sec.find("div", class_="prof_skill_uhave_col")
        right = sec.find("div", class_="prof_skill_uhave_col_right")

        if left is not None:
            for l,r in zip(left.findAll("div", class_="prof_skill_row"), right.findAll("div", "prof_skill_row")):
                skill = l.find("label", class_="prof_sk_txt").get_text(strip=True).replace(" ","_")
                have = 3 - len(l.select('span.deactive'))
                need = 3 - len(r.select('span.deactive'))

                data['skill_'+skill+'_has'] = have
                data['skill_'+skill+'_need'] = need

        data.insert({'skill_other' : sec.findAll("span", class_="single")})

    secs = soup.findAll("div", class_ = "section_box experience")
    for sec in secs:
        if sec.find(class_="icon_experience") is not None:
            exp_work = sec.find("table", class_="exp-list")
            if exp_work is not None:
                for i, w in enumerate(exp_work.findAll("tr")):
                    items = w.findAll("td")
                    data['exp_work_'+str(i)] = items[0].get_text(strip=True)
                    data['exp_work_'+str(i)+'_y'] = items[2].get_text(strip=True)

            for area in sec.findAll("div", class_="show mar_top15"):
                first_p = area.p.get_text(strip=True).lower()
                if first_p == "areas of expertise":
                    data.insert({'exp_expertise' : area.findAll("span", class_="expertise_col")})
                elif first_p == "looking expertise":
                    data.insert({'exp_expertise_look' : area.findAll("span", class_="expertise_col")})
                elif first_p == "startup experience":
                    for se in area.findAll(class_="startup_Col"):
                        data.insert({'exp_startup_' + se.find("h5").get_text(strip=True).replace(" ","_") : se.find("h2", class_="startup_txt")})       
                elif first_p == "adviser experience":
                    for se in area.findAll(class_="startup_Col"):    
                        data.insert({'exp_advisor_' + se.find("h5").get_text(strip=True).replace(" ","_") : se.find("h2", class_="startup_txt")})       
                elif first_p == "key accomplishments":
                    data.insert({'exp_key_accomplishments' : area.findAll("p")[1]}, lambda t: unicode(t.get_text()))            

        if sec.find(class_="icon_certifications") is not None:
            data.insert({"exp_certification" : sec.findAll("p")})
        if sec.find(class_="icon_accelerators") is not None:
            data.insert({"exp_accelerator" : sec.findAll("p")})

    sec = soup.find("div", class_ = "section_box looking_for")
    if sec is not None:
        #This part is for advisors
        data.insert({'looking_compensation_offer' : sec.find("p")})
        #data.insert({'looking_comp_cash' : sec.find(class_="looking_icon_01_enable")}, lambda l: l is not None)
        #data.insert({'looking_comp_share' : sec.find(class_="looking_icon_02_enable")}, lambda l: l is not None)
        #data.insert({'looking_comp_both' : sec.find(class_="looking_icon_03_enable")}, lambda l: l is not None)
        data.insert({'looking_compensation' : sec.find("p", class_="cntr")}, lambda c: c.b)    

        #Others
        for i, wc in enumerate(sec.findAll(class_="weeklyCmt")):
            if i == 0:
                if wc.span: data.insert({'looking_weekly_h_commit' : wc.span}, lambda c: c.get_text(strip=True).replace("Weekly commitmentof ", "").replace(" hours per week",""))
            if i == 1:
                if wc.span: data.insert({'looking_reward_in_return' : wc.span})

        bs = sec.find("div", class_="business_stage_tabs")
        if bs is not None: 
            for stage in bs.findAll("span", class_="active"):
                #zero indexing is hacky: breaks if class label sequence is changed
                data.insert({'looking_business_stage' : stage['class'][0]}, lambda s: s.replace("_icon",""))

    sec = soup.find("div", class_ = "section_box education")
    if sec is not None:
        i = 0
        for sb in sec.findAll("div", class_="section_box_inner"):
            l = sb.find("b", class_="f_left")
            r = sb.find("span", class_="right_txt")
            paragraph = sb.find("p")
            data.insert({'edu_school_'+str(i) : l})
            data.insert({'edu_school_'+str(i)+'_y' : r})
            data.insert({'edu_school_'+str(i)+'_summary' : paragraph}, lambda p: p.get_text(strip=False).strip())
            i += 1

    sec = soup.find("div", class_ = "section_box archetype")
    if sec is not None:
        data.insert({'archetype_desc' : sec.h3})
        content = sec.find("div", class_="archetype_cont")
        if content is not None:
            #always presume weakness / strenghts in [0] and [1]
            s, w = content.findAll("ul")
            data.insert({'archetype_strength' : s.findAll("li")})
            data.insert({'archetype_weakness' : w.findAll("li")})

    sec = soup.find("div", class_ = "section_box agegroup")
    if sec is not None:
        lu = ["<25", "25-35", "36-55", "55+"]
        data.insert({'age' : sec.find("img")}, lambda i : lu[int(i['src'].replace("level_", "").split('/')[-1][:-4])-1])

    sec = soup.find("div", class_ = "section_box social1")
    if sec is not None:
        s_classes = ['linkedin', 'facebook', 'twitter']
        s_trues = [False] * len(s_classes)
        for sp in sec.findAll("a", class_="social_profiles"):
            t = sp.find("h4").get_text(strip=True).lower()
            if t is not None:
                if t in s_classes: s_trues[s_classes.index(t)] = True
                else: "Error: new social profile found (%s)" % t
        for i, v in enumerate(s_trues): data.insert({'social_'+ s_classes[i] : s_trues[i]})

    sec = soup.find("div", class_ = "section_box video")
    data.insert({'video' : True if sec is not None else False})

    sec = soup.find("div", class_ = "events2")
    if sec is not None:
        i = 0
        for e, d in zip(sec.findAll("div", class_="event_Col hov relative"), sec.findAll("div", class_="event_Col sel_Col")):
            data.insert({'event_'+str(i) : e.find("a")})
            data.insert({'event_'+str(i)+'_desc' : d.find("h5").contents[2].strip()})
            i += 1
    
    return data


# In[13]:

db = MongoClient('localhost', MONGOPORT).cf_crawl
profiles = db.cf_profiles
#profiles.create_index("id", unique=True)

p_cursor = profiles.find({'detail_raw' : {"$exists" : True}})
if LIMIT: p_cursor = p_cursor.limit(LIMIT)
print "Processing %i profiles" % p_cursor.count()

def write_results(p_url, upd):
    data = {"$set" : upd}
    result = profiles.update_one({'url': p_url}, data, upsert=False)
    return result

import pandas as pd
full_data = []
for p in p_cursor:
    try:
        data = parse_detail(BeautifulSoup(p['detail_raw'], "lxml"))
        w = write_results(p['url'], data)
	p['name'] = p['name'].strip()
        print "(%s) processed for %i fields, mod %i" % ("http://www.cofounderslab.com"+p['url'], len(data), w.modified_count)
        #mini sanity check
        if len(data) == 0: print "ERROR, retrieved 0 fields"
        if len(data) < 128: 
        	del p['detail_raw']
        	data.update(p)
		full_data.append(p)
    except KeyboardInterrupt:
        print "Interrupted .. last url: " + "http://www.cofounderslab.com"+p['url']
        break


# In[8]:

"""p_cursor = profiles.find({'detail_raw' : {"$exists" : True}})
print "Processing %i profiles" % p_cursor.count()

#p = p_cursor.()
for p in p_cursor: 
    if 'age' in p: print p['age']
    else: print p['url']"""


# In[15]:

df = pd.DataFrame(full_data)
print "saving "+str(len(df))+" rows to "+OUT
df.to_excel(OUT+".xls")
df.to_csv(OUT+".csv", encoding="utf-8")
