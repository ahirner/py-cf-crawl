# py-cf-crawl
Fully structured retrieval of cofounderslab.com profiles in Python (mongoDB, BeautifulSoup and Scrapy).
Because data is represented differently for each profile type, searching, scraping and parsing are separated from each other. This allows to make adaptations to the final data without throwing away retrieved pages.
##Crawling Profile Summaries
###Usage
python cf-crawl.py
Make sure your mongoDB instance is accessible (port and address hardcoded). You can interrupt the process any time without loosing data.
Timestamped in "summary_retrieved".
###Tricks
Unrestricted search queries are limited to 250 pages. Thus, queries need to be mimicked by http post request to the API endpoint at /Index/postfilter and maintained in the session cache. A sequence of different filters yields a full set of profiles. These queries were obtained by intercepting post requests from a manual search and are specified in the global variable "filters".
##Crawling Profile Details
###Usage
python cf-detail-crawl.py\n
Fetches each profile url, updates them in case a user chose another profession and stores the raw html into "detail_raw" document. Specify MISSING_ONLY= True if you only want to crawl not yet retrieved profile pages.
Timestamped in "detail_retrieved".
###Tricks
Unlike the sequential requests from the initial search queries, fetching the detailed data is parallized through scrapy.
##cf-parse.py
##Usage
python cf-parse.py outname
Outputs both a outname.csv and outname.xls file.
##Tricks
Since many html branches exist only in certain types of profiles, a custom class DictData handles sparse data entry from BeautifulSoup objects gracefully with common postprocessing (stripping, flattening arrays, preprocess hooks). Thus, parsing all various fields is compact with less error handling.
