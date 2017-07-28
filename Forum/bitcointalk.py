#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')


import multiprocessing

import re
import os
import time
import csv 
import math
import logging
import requests
from platform import platform
from lxml import etree
from lxml import html
from forumlist import  *

#Parsing CLI arguments
import argparse

from dateutil.parser import parse as dateParse 
import datetime
import time

def parsedHTML(urlType, id, pageCounter):
	#This function handles the web requests and parses the HTML into an lxml tree 
	#Headers so we don't get 403 forbidden errors 
    cookies = {
        'PHPSESSID': '4iv9q9mc262v8j3vtmsrjf86r6',
    }

    headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'If-Modified-Since': 'Thu, 27 Jul 2017 18:15:14 GMT',
    }

    #Merge the topic/board ID and the page counter (40-increments) into a single identifier 
    pageIdentifier = str(id)+'.'+str(pageCounter)
    print pageIdentifier

    #To get a post, params include 'topic', and an integer, suffixed with 0 as the page counter
    params = (
        (urlType, pageIdentifier),
    )
    print params
    
    #URL for bitcointalk stays the same, just modifying the parameters 
    url = 'https://bitcointalk.org/index.php'
    page = requests.get(url, headers=headers, params=params, cookies=cookies)
    tree = html.fromstring(page.content)
    return tree

def getMaxPage(boardPage):
    #Go over all the pages with the navPages class, convert to int and pick the highest
    #Using the 'max' function
    pages = boardPage.xpath('//a[@class="navPages"]/text()')
    pages = [int(x) for x in pages if x.isdigit()]
    maxPage = max(pages)
    return maxPage

#Get topic gets individual topics, after the page has been fetched 
def getTopic(topicURL):
    #to get the topic ID we split the url twice
    topicID = topicURL.split("=")[-1].split(".")[0]
    print topicID

    tree = parsedHTML('topic',topicID, '0')

    #Get the timestamp first, if it's not from a year we want, skip it 
    try:
        timestamp = tree.xpath('//div[@class="smalltext"]')[1].text_content()
    except:
        print 'NO TIMESTAMP FOUND'
        print topicURL
        return False

    todayDate = str(time.strftime('%d %B %Y'))
    timestamp = timestamp.replace('Today', todayDate)
    timestamp = timestamp.replace(' at',",")
    timestamp = dateParse(timestamp)

    postBody = tree.xpath('//div[@class="post"]')[0].text_content()
    print postBody
    authorActivity = tree.xpath('//td[@class="poster_info"]/div[@class="smalltext"]')[0].text_content().split('Activity: ')[-1].split('\n')[0]
    
    return [postBody, timestamp, authorActivity]
    
    #[0].text_content()
def convertStringDate(timestamp):
    todayDate = str(time.strftime('%d %B %Y'))
    timestamp = timestamp.replace('Today', todayDate)
    timestamp = timestamp.replace(' at',",")
    timestamp = dateParse(timestamp)
    return timestamp

def getBoard(forumName, boardID, scrapeYears):
    #Boolean used in setting CSV header rows at the end of this function 
    first = True 
    #Get the first forum board page to get maxpages and count loops
    boardPage = parsedHTML('board', boardID,'0')
    maxPage = getMaxPage(boardPage)

    #Set a filename where we collect all the topics that are scraped
    filename = forumName+'_bitcointalk_'+str(int(time.time()))+'.csv'
    #40 posts per page, 
    loops = int(math.ceil((float(maxPage)/40)))
    for i in range(2,loops+1):

        
        #-40 because it starts at .0 on the first page 
        pageCounter = str(i*40-40)

        #Specify the type of the request, the ID, and the page counter 
        boardPage = parsedHTML('board', boardID, pageCounter)
        #Really stupid XPath selector relying on the cellpadding property... 
        items = boardPage.xpath('//table[@cellpadding="4" and @class="bordercolor"]/tr')
        #print(etree.tostring(items, pretty_print=True))
        print len(items)
        for item in items:
            #Check when the last reply was, 
            last_reply = item.xpath('./td[contains(@class, "lastpostcol")]/span')
            
            if len(last_reply) < 1:
                print ' no last reply'
                continue

            #Get the last reply time, so we can filter if it is from a year we don't want 
            last_reply = last_reply[0].text_content()
            #print(etree.tostring(item, pretty_print=True))

            #Creating a regex string from the scrapeyears 
            #IF the last reply year is below the lowest as defined in scrapeyears, ignore it
            #Input argument is in strings so have to convert it first 
            if scrapeYears:
                inputYears = [int(sYear) for sYear in scrapeYears]

                now = datetime.datetime.now()

                #Creating an 'or' regex to filter last_reply dates 
                reString = '('+str(now.year)
                for y in range(min(yearList), int(now.year)+1):
                    reString += "|"+str(sYear)
                reString += ')'

                #If the last reply is older than any of the specified years, we can be sure that the next posts will
                #Also be older (posts are ordered by last reply), and thus we can end the scraping of this board 
                if min(yearList) < convertStringDate(last_reply).year:
                    return
                #If the last reply wasn't in any of the specified years, terminate
                #Topics are ordered by reply or post date, so can just terminate if it is smaller year 
        
                if not re.search(reString, last_reply) \
                    and not re.search('(Today)', last_reply):
                    print 'skipping because of date'
                    continue

            #This try/except is a really ugly solution, but sometimes the request just errors out, or the XPath isnt found
            #Simply skipping the topic instead of creating overly complex filter functions for these edge cases 
            try:
                topicTitle = item.xpath('td/span[contains(@id, "msg_")]/a')[0].text_content()
                print topicTitle
                author = item.xpath('td/a[contains(@title, "View the profile of")]')[0].text_content()
                print author
                topicURL = item.xpath('td/span[contains(@id, "msg_")]/a')[0].get('href')
                print topicURL
                totalReplies = int(item.xpath('td')[4].text_content().replace(" ", ""))
                print totalReplies
            except:
                continue


            #Collect the topic post text and author activity, as well as the topic start date 
            topic = getTopic(topicURL)

            #If any of the above attributes isn't found in the getTopic function, move on 
            if not topic:
                continue 

            #We now have the topic start date; if it wasnt started in a specified year, move on 
            if scrapeYears and str(topic[1].year) not in scrapeYears:
                continue
            
            authorActivity = topic[2]
            timestamp = topic[1]
            topicBody = topic[0]

            csvwriter = csv.writer(open(filename, "a"))
            #If this is the first row we're writing to this CSV, drop in some headers for each column 
            if first:
                csvwriter.writerow(['timestamp', 'author', 'authorActivity', 'topicTitle', 'totalReplies', 'topicURL', 'topicBody'])
                first = False
            csvwriter.writerow([timestamp, author, authorActivity, topicTitle, totalReplies, topicURL, topicBody])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape news articles')
    parser.add_argument('--years', nargs='+', dest="scrapeYears", help='Specify the years you want to collect from', required=False)
    parser.add_argument('--boards', nargs='+', dest="sources", help='Set the forum boards you want to collect from', required=True)
    args = parser.parse_args()

    print args.scrapeYears
    print args.sources
    scrapeYears = args.scrapeYears
    scrapeBoards = args.sources


    for board in scrapeBoards:
        #Using multiprocessing to speed things up a little. Creates new process thread for every source channel/forum board
        #For that reason, maybe not scrape too many discussion boards at once
		#Calling getBoards also calls its child function that collects topics 
		p = multiprocessing.Process(target=getBoard, args=(board, forumIDs[board], scrapeYears))
		p.start()
		print 'started thread for %s topics' % board
