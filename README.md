# Structured retrieval of [cofounderslab](https://cofounderslab.com) profiles in Python 
... with [pymongo](https://api.mongodb.org/python/current/), [BeautifulSoup](https://pypi.python.org/pypi/BeautifulSoup/) and [Scrapy](http://scrapy.org). <br>
Because data is represented differently for each profile type, the process is split up into three steps: 
1. searching 
2. scraping 
3. parsing and output
This allows to make adaptations for the final output without throwing away retrieved pages.
##Searching for Profile Summaries
####Usage
`python cf-crawl.py` <br>
Make sure your mongoDB instance is accessible (port and URL hardcoded). You can interrupt the process any time without loosing data. <br>
Timestamped in "summary_retrieved".
####Tricks
Unrestricted search queries are limited to 250 pages. Thus, queries need to be mimicked by http post request to the API endpoint at /Index/postfilter and maintained in the session cache. A sequence of different filters yields a full set of profiles. These queries were obtained by intercepting post requests from a manual search and are specified in the global variable "filters". <br>
!["capturing filter requests as json items"](./screens/http_post_request_capture.png?raw=true "capturing filter requests as json items")
*How to capture search filter requests as json items: applied filter and json string (green), screenshot of browser view (red)* <br><br>
Additionally, session variables must be maintained throughout the process. We use [requests](https://github.com/kennethreitz/requests)' session method for that.
##Scraping Profile Details
####Usage
`python cf-detail-crawl.py` <br>
Fetches each profile url, updates them in case a user chose another profession and stores the raw html into "detail_raw" document. Specify MISSING_ONLY= True if you only want to crawl not yet retrieved profile pages. <br>
Timestamped in "detail_retrieved".
####Tricks
Unlike the sequential requests from the initial search queries, fetching the detailed data is parallized through scrapy.
##Parsing and Output
####Usage
`python cf-parse.py outname` <br>
Updateds database and outputs both a outname.csv and outname.xls file. All field names are defined in parse_detail(soup).
####Tricks
Since many html branches exist only in certain types of profiles, a custom class DictData handles sparse data entry from BeautifulSoup objects gracefully with common postprocessing (stripping, flattening arrays, preprocess hooks). Thus, parsing a combined set of fields is compact.
