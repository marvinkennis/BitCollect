#!/usr/bin/env python
#-*- coding:utf-8 -*-

# The scrapeconfig.py config file contains all xpaths for the websites that are being scraped 
# Since this scraper is modular, you can edit the scrapeconfig.py file to use this 
# scraper to collect data from ANY news website with a results and article page
# Just make sure you set correct XPaths for the properties you want to collect 
from scrapeconfig import *

import multiprocessing

#regex for some string locations 
import re 
import requests
import json

#Parsing CLI arguments
import argparse

#LXML as main HTML parser. Has nice Xpath selection, works everywhere 
from lxml import html
from lxml import etree

#dateparser to handle different types of date formats on articles 
from dateutil.parser import parse as dateParse 

import csv 
import time 

#Setting default to UTF8 to deal with pesky ascii errors in python 2.x
import sys;
reload(sys);
sys.setdefaultencoding("utf8")

def parsedHTML(url):
	#This function handles the web requests and parses the HTML into an lxml tree 
	#Headers so we don't get 403 forbidden errors 
	headers = {
		'accept-encoding': 'gzip, deflate, br',
		'accept-language': 'en-US,en;q=0.8',
		'upgrade-insecure-requests': '1',
		'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
		'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		'cache-control': 'max-age=0',
		'authority': 'news.bitcoin.com',
		'cookie': '__cfduid=d784026513c887ec39604c0f35333bb231500736652; PHPSESSID=el5c5j7a26njfvoe2dh6fnrer3; _ga=GA1.2.552908756.1500736659; _gid=GA1.2.2050113212.1500736659',
	}
	page = requests.get(url, headers=headers)
	tree = html.fromstring(page.content)
	return tree

def collectArticles(urls, source, args, filename):
	#Loop over all the URLS that were collected in the parent function 
	for url in urls: 

		tree = parsedHTML(url)

		#Initialize empty text string, add paragraphs when collected 
		articleText = ""

		#The function that is called here is from the scrapeconfig.py file (imported)
		#Have to pass the tree along with the source key, otherwise it cant access xpaths 
		print url
		config = pageConfig(source, tree)

		#If page was not found, continue to next URL 
		if not config:
			continue

		#Based on xpaths defined above, call correct selector for current source
		#Could just pass the config selectors to the array, but for the sake of cleanliness...
		
		articleTitle = config['articleTitle']
		articleText = config['articleText']
		articleAuthor = config['articleAuthor']
		#Storing it as a datetime object 
		articleDate = config['articleDate']

		#Check against the year argument, terminate if it turns out the year for the current 
		#article is < than the year you want to collect from (no point in continuing then)
		#if it does not match, don't write, if it's smaller, terminate 
		if args.scrapeYear and dateParse(articleDate).year() < int(args.scrapeYear):
			break
		elif args.scrapeYear and dateParse(articleDate).year() != int(args.scrapeYear):
			pass
		else:
			csvwriter = csv.writer(open(filename, "a"))
			csvwriter.writerow([articleDate, articleTitle, articleAuthor, url, articleText])

		


def getArticleURLS(source, args):
	#Create filename where everything is stored eventually. Doing str(int()) so the time is rounded off
	filename = source+'_ARTICLES_'+str(int(time.time()))+'.csv'
	urls = []
	currentPage = 1
	print currentPage
	hasNextPage = True
	outOfRange = False
	while hasNextPage and not outOfRange:
		print 'setting dict'
		#Parse HTML, invoke config (x)paths 
		tree = parsedHTML(resultsConfig(currentPage)[source]['pageURL'])
		items = tree.xpath(resultsConfig(currentPage)[source]['itemXpath'])

		print 'looping over items'
		#For every item on the search results page... 
		for item in items:
			#Here we invoke the correct Xpaths from the config dict above 

			#Not every results page correctly displays datetime in result, so if it's not here
			#do the check when fetching the articles. Else, if its ordered by date just terminate if the current article date is < the year youre scraping
			if resultsConfig(currentPage)[source]['dateOnPage'] and resultsConfig(currentPage)[source]['dateOrdered'] and args.scrapeYear:
				articleDate = dateParser(item.xpath(resultsConfig(currentPage)[source]['dateXpath'])[0].get('datetime'))
				
				#If we already see that the article date is not from a year we want to collect (eg if from 2014 and 2015 was specified)
				#then we just terminate the while loop. Only works one way, as articles are ordered by date, so can only do if smaller 
				if articleDate.year() < int(args.scrapeYear):
					outOfRange = True 
				#Note that it then just terminates on the next page (since there is no 'break' statement for the while loop)

			articleURL = item.xpath(resultsConfig(currentPage)[source]['urlXpath'])[0].get('href')
			
			#Some websites have relative URL pointers, so prefix the base URL 
			if '://' not in articleURL:
				articleURL = resultsConfig(currentPage)[source]['baseURL']+articleURL

			#Urlfilter hack to prevent video/audio/gadfly pages from being visited (mostly bloomberg)
			#These pages have custom xpath structures, so not even bothering collecting them
			urlFilters = ['/videos/','/audio/','/gadfly/','/features/','/press-releases/']
			#If any of the above strings is in the url, pass writing it, else write it 
			if any(urlFilter in articleURL for urlFilter in urlFilters):
				pass
			else:
				urls.append(articleURL)

		#If there are less items in the results than the resultsPerPage param, we assume this is the last page 
		if len(items) < resultsConfig(currentPage)[source]['resultsPerPage']:
			hasNextPage = False 

		#Increase page number by 1 for the next iteration of the while loop 
		currentPage += 1

		#Once all URLs for the page have been collected, go visit the actual articles 
		#Do this here so it doesn't first collect too many URLs that are useless afterwards 
		collectArticles(urls, source, args, filename)
		#Reinitialize URLS array again for next loop 
		urls = []


if __name__ == '__main__':

	#Neat way of inputting CLI arguments 
	parser = argparse.ArgumentParser(description='Scrape news articles')
	parser.add_argument("--year", dest="scrapeYear", required=False, help="Specify a specific year to collect from")
	parser.add_argument('--sources', nargs='+', dest="sources", help='Set the news websites you want to collect from', required=False)
	args = parser.parse_args()
	print args.scrapeYear
	print args.sources

	#Check if some sources are defined as input argument, otherwise just go over all 
	allSources = ['coindesk','reuters','newsbitcoin','wsj','cnbc','bloomberg']
	if args.sources:
		visitSources = args.sources
	else:
		visitSources = allSources

	for source in visitSources:		
		#Using multiprocessing to speed things up a little. Creates new process thread for every source channel o
		#Calling getArticleURLS will also call child function that collects the actual articles 
		p = multiprocessing.Process(target=getArticleURLS, args=(source, args))
		p.start()
		print 'started thread'






