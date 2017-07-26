#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import re
import os
import time
import logging
from platform import platform
from lxml import etree
from forumlist import  *

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


#Bitcointalk is a mess, impossible to capture with normal requests so resorting to 
#browser simulation with Selenium + phantomJS; downside: super super slow 
def getPhantomJS():

    service_args = [
        '--load-images=false',
        '--disk-cache=true',
    ]

    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 Safari/537.36"
    )

    phantomjs_path = os.path.join(os.getcwd(), 'phantomjs')

    browser = webdriver.PhantomJS(executable_path='./phantomjs',
        service_args = service_args, desired_capabilities = dcap)
    return browser

def getMaxPage(sel):
    pages = sel.xpath('//a[@class="navPages"]/text()')
    pages = [int(x) for x in pages if x.isdigit()]
    maxPage = max(pages)
    return maxPage

def getTopic(browser, startURL, result):

    logging.debug('ready to scrape topic => %s', result['topicTitle'])
    logging.debug('topic url => %s', startURL)

    startURL += ';all'
    browser.get(startURL)
    sel = etree.HTML(browser.page_source)
    items = sel.xpath('//form[@id="quickModForm"]/table/tbody/tr')

    activities = re.findall('Activity: ([0-9]+)', browser.page_source, re.S)
    if not activities:
        result['replies'] = []
        logging.error('failed to scrape replies => %s', result['topicTitle'])
        logging.error('topic url => %s', startURL)
        return

    body = sel.xpath('//*[@id="quickModForm"]/table[1]/tbody/tr[1]/td/table/tbody/tr/td/table/tbody/tr[1]/td[2]/div/text()')
    authorActivity = activities[0]
    result['body'] = body

    topicdate = sel.xpath('//*[@id="quickModForm"]/table[1]/tbody/tr[1]/td/table/tbody/tr/td/table/tbody/tr[1]/td[2]/table/tbody/tr/td[2]/div[2]/text()')
    print topicdate
    result['topicdate'] = topicdate
    result['authorActivity'] = int(authorActivity)
    topictitle = sel.xpath('//*[@id="bodyarea"]/div[1]/div/b[4]/a/text()')
    print topictitle
    authorItem = items[0]
    timestamp = authorItem.xpath('.//td[@class="td_headerandpost"]//tr/td[2]/div[2]/text()')
    if not timestamp:
        timestamp = authorItem.xpath('.//td[@class="td_headerandpost"]//tr/td[2]/div[2]/span/text()')

    timestamp = timestamp[0]

    #only created in 2015 will be handled
    if not re.search('(2015)', timestamp):
        result = {}
        return

    result['timestamp'] = timestamp
    result['topictitle']

    items = items[1:]
    replies = []

    index = 1

    for item in items:
        author = item.xpath('.//td[@class="poster_info"]/b/a/text()')
        if not author:continue
        author = author[0]

        timestamp = item.xpath('.//td[@class="td_headerandpost"]//tr/td[2]/div[2]/text()')
        if not timestamp:continue
        timestamp = timestamp[0]

        if not re.search('([A|P]M)', timestamp):continue

        #only posted in 2015 will be handled
        if not re.search('(2015)', timestamp):continue

        text = item.xpath('.//td[@class="td_headerandpost"]//div[@class="post"]/text()')
        if text:
            text = text[0]

        reply = {}
        reply['author'] = author
        reply['timestamp'] = timestamp
        reply['authorActivity'] = int(activities[index])
        reply['text'] = text
        replies.append(reply)

    result['replies'] = replies

def getPage(browser, sel):
    if sel.xpath('//td[text()="Child Boards"]'):
        items = sel.xpath('//div[@id="bodyarea"]/div[3]/table/tbody/tr')
    else:
        items = sel.xpath('//div[@id="bodyarea"]/div[2]/table/tbody/tr')

    pageResult = []
    for item in items:

        last_reply = item.xpath('td[7]/span/text()')
        if not last_reply: continue

        last_reply = last_reply[0]
        if not re.search('(201[5|6|7])', last_reply) \
            and not re.search('(Today)', last_reply):
            continue

        result = {}
        topicTitle = item.xpath('td[3]/span/a/text()')
        author = item.xpath('td[4]/a/text()')
        topic_url = item.xpath('td[3]/span/a/@href')
        TotalReplies = item.xpath('td[5]/text()')

        if not topicTitle \
            or not author \
            or not topic_url \
            or not TotalReplies:
            continue

        topic_url = topic_url[0]
        topicTitle = topicTitle[0]
        author = author[0]
        TotalReplies = TotalReplies[0]

        result['topicTitle'] = topicTitle
        print topicTitle
        result['author'] = author
        result['topic_url'] = topic_url
        result['TotalReplies'] = int(TotalReplies)

        getTopic(browser, topic_url, result)
        time.sleep(1)

        #now only scrape 2015
        if result:
            pageResult.append(result)

    return pageResult

def getForum(browser, name, startURL):

    logging.info('ready to scrape forum => %s', name)
    logging.info('forum url => %s', startURL)

    browser.get(startURL)
    sel = etree.HTML(browser.page_source)
    maxPage = getMaxPage(sel)

    output = []

    pageURL = startURL
    fileName = name.replace(' ', '_')
    fileName += '.txt'
    for i in range(2, maxPage + 1):
        pageResult = getPage(browser, sel)
        if pageResult:
            output.extend(pageResult)

        with open(fileName, 'wb') as f:
            f.write(str(output))
            f.close()

        pageURL = sel.xpath('//td[@id="toppages"]/a[text()=%d]/@href' % i)
        if not pageURL:
            logging.error('failed to get page => %d', i)
            break
        pageURL = pageURL[0]
        browser.get(pageURL)
        sel = etree.HTML(browser.page_source)

    with open(fileName, 'wb') as f:
        f.write(str(output))
        f.close()

    logging.info('successfully scrape forum =>%s', name)

def getConfig():
    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s [line:%(lineno)d] %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S')

def run():

    getConfig()
    browser = getPhantomJS()

    for forumName, forumUrl in forums.items():
        start = time.clock()
        getForum(browser, forumName, forumUrl)
        stop = time.clock()
        logging.info('scrape forum => %s cost %f sec', forumName, stop - start)

    browser.quit()

if __name__ == '__main__':
    run()

