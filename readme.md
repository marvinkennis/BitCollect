This repository contains four different scrapers for Bitcoin-related data collection. 

## IRC
The IRC scraper collects data through the bitcoinstats IRC archive and is the most straightforward scraper included in this repo. The Bitcoin IRC archive contains the #otc and #dev channels. To collect data, specify both the channel and the year from which you want to collect data: 
```
python IRCScraper.py otc 2015 
```
The above command would collect data from the #otc channel over 2015. It collects the message text, author, and timestamp for each IRC message. 

The IRC scraper has the following (external) python package dependencies, each of which can be installed using pip: 
- urllib2 
- bs4

Output is written to CSV files.


## News 
The news scraper collects news articles from CNBC, News.Bitcoin.com, Bloomberg, Wallstreet Journal, Reuters, and Coindesk. You can specify which of these you want to include/exclude in your data collection.  As a general pattern, this scraper first traverses all pages on each site's search results, collects the URLs for the articles, and then collects the actual article data. It collects the actual articles after every search result page, then goes to the next search results page to gather more URLs to visit. 

In general, this scraper is pretty flexible and easy to adapt when a site changes. The code includes two config dictionaries where you can edit the XPaths for the site elements. Editing those breaks nothing else. These dictionaries are found in the scrapeconfig.py file. 

The news scraper uses multiprocessing and creates a separate thread for every source you are scraping. This greatly speeds up the data collection. 


### Execution
This scraper has two (optional) input arguments when you run it from the command line: 
--year (will then only collect data from this year)
--sources (allows you to en)

You can input anything reasonable in year, but sources is currently limited to the following: 
- wsj (WallStreet Journal)
- bloomberg (Bloomberg)
- reuters (Reuters)
- newsbitcoin (News.Bitcoin.Com)
- coindesk (Coindesk)
- cnbc (CNBC)

You can then run it by doing:
```
python News.py --year 2015 --sources coindesk reuters wsj 
```
This would then collect articles from 2015 from coindesk, reuters, and the wallstreet journal. 

You can also leave the arguments out and simply run
```
python News.py
```
which would collect all articles, from all sources, over all years. Output is written to timestamped CSV files, split up per publisher/source 

### Adding new websites to the news scraper 
In order to use this scraper to collect data from other news websites, you have to define respective XPaths for the relevant elements on the search results and articles page. The required dictionary keys / xpath definitions are explained in the scrapeconfig.py file. Simply copy the a dictionary entry in the pageConfig and resultsConfig dictionaries and fill them out with the correct data. This required you to be somewhat familiar with how xpaths work. 

## Reddit 
TBA

## Forum 
This scraper collects data from the Bitcointalk.org forum. Just note that this one is incredibly slow. Bitcointalk has no nice search or filter function, so we have to visit all posts on the selected boards, check their dates, and go from there. Furthermore, Bitcointalk doesn't work well with Python requests, so this scraper resorts to selenium + ghostdriver. The binary is included. 