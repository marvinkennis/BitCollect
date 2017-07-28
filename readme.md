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

**Note that the code for this scraper is very heavily commented, which in itself step by step explains how it works in detail**

In general, this scraper is pretty flexible and easy to adapt when a site changes. The code includes two config dictionaries where you can edit the XPaths for the site elements. Editing those breaks nothing else. These dictionaries are found in the scrapeconfig.py file. 

The news scraper uses multiprocessing and creates a separate thread for every source you are scraping. This greatly speeds up the data collection. 


### Usage
This scraper has two (optional) input arguments when you run it from the command line: 
--year (will then only collect data from this year)
--sources (allows you to limit data collection to specific news channels)

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
This reddit scraper works for *any* subreddit. Simply specify the subreddit with the (required) --subreddit argument. NOTE: You will have to use your own Reddit account (username and password) and Reddit API key to use this scraper. It only collects the parent post text (if available), title, creation date, author, and score, but it really is quite fast. Benchmarked it at around 3K posts/minute. 

### Create a new Reddit application and configure the settings.py file 
Once logged into your account, go to https://www.reddit.com/prefs/apps/ and click on 'create a new app'. Fill in the relevant information and make sure you set the application type to 'script application'. The client ID and secret key can then be entered into the config dictionary in the settings.py file, along with your Reddit username and password - I suggest just making a new account for this. The Reddit account of which you enter the credentials needs to be the same as the account on which you have created the API/application keys. 

#### (required) Input argument: --subreddit
URL extension of the subreddit you want to scrape, basically just the part that comes after reddit.com/r/...

#### (required) Input argument: --year
You have to specify a specific year to collect posts from. This scraper uses the CloudSearch reddit search endpoint to search between a window of two time intervals.

#### (required) Input argument: --timestamp_interval 
This is the size of the sliding window that is used to fetch Reddit search results, specified in epochs. Selecting the right interval for your subreddit depends on the amount of posts in the subreddit. The API returns at most 100 posts per query. So for larger subreddits with a higher post frequency, you should select a smaller interval. If you don't, the API might not return all posts made in that interval, since it only returns 100 results. Only downside to a smaller interval. I typically set it to 20000. 

### Usage 
Example launch command: 
```
python Reddit.py --subreddit btc --year 2015 --timestamp_interval 20000 
```
The above command will collect Reddit posts from the /r/btc subreddit over 2015, using a 20000 epoch timestamp interval sliding window when fetching results. 

## Forum 
This scraper collects data from the Bitcointalk.org forum.  Bitcointalk has no nice search or filter function, so we have to visit all posts on the selected boards, check their dates, and go from there. 

Just like with the news scraper, a separate 'config' file is included that tells the scraper which forum boards to collect data from, and what the PHPBB ID's for these forums are. Edit the dictionary in the *forumlist.py* file with the title and correct board ID. Board URLS have to following format: https://bitcointalk.org/index.php?board=8.0. You would only specify '8' as the board ID to collect posts from this board

### Usage 
The forum scraper has two input arguments: 
#### Input argument: --boards
This takes either a single forum board or list of boards as input. *You have to make sure you specify the board names in the argument exactly as they are listed in the forumlist.py file* 

The following forum boards are currently included in the file, but other boards can be added by adding a dictionary entry in *forumlist.py*.
- discussion
- development_technical
- mining
- techsupport
- projectdevelopment
- economics
- marketplace
- meta
- politics_society
- beginners_help
- offtopic
- altcoins
- trading

The below command will collect all topics from all years from the discussion, trading, and economics forum boards. Specifying a forum board is required for the scraper to start.
```
python bitcointalk.py --boards discussion trading economics 
```
If you specify multiple boards, the program will start a separate thread for each board using multiprocessing. Although it is incredibly fast, I would not recommend starting too many threads simultaneously, as, for reasons unknown to me, it increases the error-rate in collecting the topic attributes. 

#### Input argument: --years 
Here you can specify a single year, or a list of years. Since the bitcointalk forums are ordered by last reply and the topic start date is not displayed in the results, almost all posts starting from the first results page will have to be visited anyways. So you might as well just collect everything and filter from the resulting CSV files.  

```
python bitcointalk.py --boards discussion --years 2016 2017  
```

The above command will collect only topics from the 'Discussions' board that were started in 2016 and 2017. 
