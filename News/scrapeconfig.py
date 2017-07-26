#Predefine xpath selectors for article info we want to scrape here.
#These are basically the structure configs for each separate website  
#Change these in case the website changes; modular, doesn't break anything else 
#References parsed LXML tree, so just putting it in the loop for now 
#Need to do if statements, otherwise you'd get list index errors 
def pageConfig(source, tree):

	#Sometimes a link is broken and it returns a 404, just checking page title 
	#and returning a False for the config 
	pageTitle = tree.find(".//title").text
	notFoundFilters = ['404', 'Not Found','Not found']
	if any(notFoundFilter in pageTitle for notFoundFilter in notFoundFilters):
		return False 

	#In general, we find all paragraphs in the article body section, and then just merge them with join
	if source == 'newsbitcoin':
		config = {'articleTitle': tree.xpath('//h1[@class="entry-title"]')[0].text,
							'articleText': " ".join(str(paragraph.text_content()) for paragraph in tree.xpath('//div[@class="td-post-content"]/p')),
							'articleAuthor': " & ".join(str(author.text) for author in tree.xpath('//div[@class="td-post-author-name"]/a')),
							'articleDate': tree.xpath('//meta[@property="article:published_time"]')[0].get('content')}
	
	#Also doing the join for authors, as there might be more than one, or none at all
	elif source == 'bloomberg':
		config = {'articleTitle':tree.xpath('//h1[contains(@class, "__hed")]/span')[0].text,
							'articleText':" ".join(str(paragraph.text_content()) for paragraph in tree.xpath('//div[@class="body-copy"]/p')),
							'articleAuthor':" & ".join(str(author.text) for author in tree.xpath('//div[@class="author"]')),
							'articleDate':tree.xpath('//time[@class="article-timestamp"]')[0].get('datetime')}

	#Reuters seems to append random chars to div classes, so use regexp 'contains' to bypass 
	elif source == 'reuters':
		config = {'articleTitle':tree.xpath('//h1')[0].text,
							'articleText':" ".join(str(paragraph.text_content()) for paragraph in tree.xpath('//div[contains(@class, "ArticleBody_body_")]/p')),
							'articleAuthor':" & ".join(str(author.text) for author in tree.xpath('//p[contains(@class, "ArticleHeader_byline_")]/a')),
							'articleDate':tree.xpath('//div[contains(@class, "ArticleHeader_date_")]')[0].text}
	
	#NOTE: WSJ has a paywall - if you want the full article text, set the appropriate headers and cookies in parseHTML function (I don't have them)
	#For now, only the article snippet will be collected
	elif source == 'wsj':
		config = {'articleTitle':tree.xpath('//h1[@class="wsj-article-headline"]')[0].text,
							'articleText':" ".join(str(paragraph.text_content()) for paragraph in tree.xpath('//div[@class="wsj-snippet-body"]/p')),
							'articleAuthor':" & ".join(str(author.text) for author in tree.xpath('//span[@class="name"]')),
							'articleDate':tree.xpath('//time[@class="timestamp"]')[0].text}
	
	elif source == 'cnbc':
		config = {'articleTitle':tree.xpath('//h1[@class="title"]')[0].text,
							'articleText':" ".join(str(paragraph.text_content()) for paragraph in tree.xpath('//div[@itemprop="articleBody"]/p')),
							'articleAuthor':" & ".join(str(author.text) for author in tree.xpath('//span[@itemprop="name"]')),
							'articleDate':tree.xpath('//time[@class="datestamp"]')[0].get('datetime')}
	
	elif source == 'coindesk':
		config = {'articleTitle':tree.xpath('//h3[@class="featured-article-title"]')[0].text,
							'articleText':" ".join(str(paragraph.text_content()) for paragraph in tree.xpath('//div[@class="article-content-container noskimwords"]/p')),
							'articleAuthor':" & ".join(str(author.text) for author in tree.xpath('//div[@class="article-meta"]/p[@class="timeauthor"]/a')),
							'articleDate':tree.xpath('//div[@class="article-meta"]/p[@class="timeauthor"]/time')[0].get('datetime')}
	else:
		sys.exit('Source channel for this article not defined, check collectArticles() function')
	
	#Return it here instead of inside if-statement, will terminate before anyways if no config is found 
	return config

#Another config dict for the results pages. Contains iterative URL and xpath for items, individual URL (relative), and date 
#At this point, all the Xpath references are strings, so they aren't called yet 
#Because they aren't called directly, we don't need to use if-statements like we do above 

#The dateOnPage key states whether it is possible to collect datetime objects from the results page, if not get it from the article page
#Needs currentPage parameter, otherwise the pageURL reference breaks 

'''
Config dict keys:
# - pageURL: numerative URL with increasing page count
# - itemXpath: XPath for the search result item container 
# - urlXpath: XPath for URL to full article, relative from itemXpath (./)
# - dateXpath: XPath for article date, will look for datetime object. Will allow scraper to terminate if it is in a date range you do not want to collect
# - dateOrdered: Simply states whether search results are ordered by date (descending)
# - dateOnPage: States whether the search result has a datetime object. If not, get the actual date from full article page 
# - resultsPerPage: How many results are shown per page, used to terminate at the last page (results < n)
'''

def resultsConfig(currentPage):
	#Split variabl assignment and return, otherwise the currentPage is undefined upon return 
	config = {'coindesk':{'pageURL':'https://www.coindesk.com/page/'+str(currentPage)+'/?s=bitcoin',
						'itemXpath':'//div[@class="post-info"]',
						'urlXpath':'./h3/a',
						'dateOnPage':True,
						'dateOrdered':True,
						'baseURL':'https://coindesk.com',
						'resultsPerPage':10,
						'dateXpath':'./p[@class="timeauthor"]/time'},

				'bloomberg':{'pageURL':'https://www.bloomberg.com/search?query=Bitcoin&page='+str(currentPage),
						'itemXpath':'//div[@class="search-result-story__container"]',
						'urlXpath':'./h1/a',
						'dateOnPage':True,
						'dateOrdered':True,
						'baseURL':'https://www.bloomberg.com',
						'resultsPerPage':10,
						'dateXpath':'./div[@class="search-result-story__metadata"]/span[@class="metadata-timestamp"]/time'},
				
				'reuters':{'pageURL':'http://www.reuters.com/search/news?blob=bitcoin&sortBy=date&dateRange=all&pn='+str(currentPage),
						'itemXpath':'//div[@class="search-result-content"]',
						'urlXpath':'./h3/a',
						'dateOnPage':False,
						'dateOrdered':True,
						'baseURL':'http://www.reuters.com',
						'resultsPerPage':10,
						'dateXpath':'HERE'},
				
				'wsj':{'pageURL':'https://www.wsj.com/search/term.html?KEYWORDS=Bitcoin&min-date=2010/07/24&max-date=2017/07/24&daysback=4y&isAdvanced=true&andor=AND&sort=date-desc&source=wsjarticle&page='+str(currentPage),
						'itemXpath':'//div[@class="headline-container"]',
						'urlXpath':'./h3/a',
						'dateOnPage':False,
						'baseURL':'https://wsj.com',
						'dateOrdered':True,
						'resultsPerPage':20,
						'dateXpath':'./div[@class="article-info"]/ul/li/time[@class="date-stamp-container highlight"]'},
				
				'cnbc':{'pageURL':'http://search.cnbc.com/rs/search/view.html?partnerId=2000&keywords=BITCOIN&sort=date&type=news&source=CNBC.com,The%20Reformed%20Broker,Buzzfeed,Estimize,Curbed,Polygon,Racked,Eater,SB%20Nation,Vox,The%20Verge,Recode,Breakingviews,NBC%20News,The%20Today%20Show,Fiscal%20Times,The%20New%20York%20Times,Financial%20Times,USA%20Today&assettype=partnerstory,blogpost,wirestory,cnbcnewsstory&pubtime=0&pubfreq=a&page='+str(currentPage),
						'itemXpath':'//div[@class="searchResultCard"]',
						'urlXpath':'./h3/a',
						'dateOnPage':False,
						'dateOrdered':True,
						'baseURL':'http://cnbc.com',
						'resultsPerPage':10,
						'dateXpath':'./time'},
				
				'newsbitcoin':{'pageURL':'https://news.bitcoin.com/page/'+str(currentPage)+'/?s=Bitcoin',
						'itemXpath':'//div[@class="item-details"]',
						'urlXpath':'./h3/a',
						'dateOnPage':True,
						'dateOrdered':True,
						'baseURL':'https://news.bitcoin.com',
						'resultsPerPage':10,
						'dateXpath':'./div[@class="td-module-meta-info"]/span/time'}
				}
	return config

