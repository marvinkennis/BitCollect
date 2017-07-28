import logging
import settings
#CLI input
import argparse
import time

#reddit api (Python Reddit API Wrapper)
import praw
import os

import datetime

#JSON parsing
import json

import time
#Multithreading and CSV processing 
from multiprocessing import Process
import csv

#Setting default to UTF8 to deal with pesky ascii errors in python 2.x
import sys
reload(sys)
sys.setdefaultencoding("utf8")

#Change this to CSV writer
def saveSubmission(submission, filename):
    #Reddit accounts can be deleted, and then the username won't show. If it doesn't exist fill in [deleted]
    if not submission.author:
        name = '[deleted]'
    #Otherwise just assign the author name 
    else:
        name = submission.author.name

    #Write it to a CSV 
    csvwriter = csv.writer(open(filename, "a"))
    csvwriter.writerow([datetime.datetime.fromtimestamp(submission.created).strftime('%c'), submission.permalink,  name, submission.title, submission.selftext, submission.score])

# Downloads all the self posts from given subreddit
# ts_interval - the interval in seconds for each request cycle
# largest_timestamp - if not set, is set to 12 hours from now.
def getThreads(subredditName, ts_interval, ep1, ep2, user_ag, user):
    #Set filename for this subreddit. Timestamp it so everytime this script is run, results are appended to differnt file 
    filename = 'Reddit_'+subredditName+'_'+str(int(time.time()))+'.csv'

    #Creating header rows in the CSV file 
    csvwriter = csv.writer(open(filename, "a"))
    csvwriter.writerow(['timestamp', 'url',  'author', 'postTitle', 'postContent', 'score'])
    #Initialize the Reddit client with client ID, secret key, user agent (arbitrary), password and username
    #See the included readme for detailed explanation 
    reddit = praw.Reddit(client_id=user['clientID'],client_secret=user['secretKey'],user_agent=user_ag,password=user['password'],username=user['username'])
    print(reddit.user.me())
    #If no time epoch is specified, 
    if ep2 is None:
        ep2 = int(time.time()) + 12*3600

    #cts for current timestamp. Defines the sliding window between which the search query is executed. 
    cts2 = ep2
    #Substract the ts interval from the second timstamp to move the window
    cts1 = ep2 - ts_interval
    currentTSInterval = ts_interval
    while True:
        #Use reddit search API to search for posts between two timestamps (created above), on the subreddit defined in subRedditName
        #Using cloudsearch as syntax, because otherwise it is not possible to search between timestamps 
        try:
            searchResults = list(reddit.subreddit(subredditName).search('timestamp:{}..{}'.format(cts1, cts2), syntax='cloudsearch'))
        #If it errors for whatever reason, log the error and continue 
        except Exception as e:
            logging.exception(e)
            continue

        #logging.debug("Got {} submissions in interval {}..{}".format(len(searchResults), cts1, cts2))
        #It returns at most 100 search results, so if it maxes out, we split the interval and search again 
        #This way we ensure that we do not miss any posts 
        if len(searchResults) == 100:
            currentTSInterval /= 2
            cts1 = cts2 - currentTSInterval
           # logging.debug("Reducing time interval to {}".format(currentTSInterval))
            continue

        #Printing Reddit post title to show progress 
        for submission in searchResults:
            print submission.title
            saveSubmission(submission, filename)

        #Move the timestamp window by setting the second ts to the first, and decreasing the second one
        cts2 = cts1
        cts1 = max(ep1, cts2 - currentTSInterval)

        #Once the timestamps meet, the range is effectively closed and no more topics are to be collected 
        if cts1 == cts2:
            break

        if len(searchResults) <= 7:
            currentTSInterval *= 2
           # logging.debug("Increasing time interval to {}".format(currentTSInterval))

def main():
    parser = argparse.ArgumentParser(description='Parallel Subreddit Downloader')
    parser.add_argument("--subreddit", dest="subreddit", required=True, help="Download the whole subreddit")
    parser.add_argument("--timestamp_interval", dest="timestamp_interval", type=int, required=True)
    parser.add_argument("--year", dest="collect_year", type=int, required=True)
    argsx = parser.parse_args()
    collect_year = str(argsx.collect_year)


    #Timeframe between which to scrape
    tst1 = '01.01.'+collect_year+' 00:00:00'
    tst2 = '31.12.'+collect_year+' 23:59:59'
    pattern = '%d.%m.%Y %H:%M:%S'

    #Timezone definition, OS based
    os.environ['TZ'] = 'UTC'

    #Convert time string to epoch 
    epoch1 = int(time.mktime(time.strptime(tst1, pattern)))
    epoch2 = int(time.mktime(time.strptime(tst2, pattern)))

    #Split the increments over 8 different multithreading processes for increased speed 
    inc = (epoch2 - epoch1 + 1)/8
    ep1 = [0]*8
    ep2 = [0]*8
    processes = []

    for i in range(0, 8):
        ep1[i] = epoch1 + i*inc
        ep2[i] = epoch1 + (i + 1)*inc - 1
        user_agx = 'Collection' + str(i)
        user = settings.config
        p = Process(target=getThreads, args=(argsx.subreddit, argsx.timestamp_interval, ep1[i], ep2[i], user_agx, user))
        p.start()
        processes.append(p)

if __name__ == "__main__":
	start = time.time()
	main()
	end = time.time()
	print end - start
	
