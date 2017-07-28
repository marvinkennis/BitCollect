import logging

#CLI input
import argparse
import time

#reddit api (Python Reddit API Wrapper)
import praw
import os

#JSON parsing
import json

#Multithreading and CSV processing 
from multiprocessing import Process
import csv

#Setting default to UTF8 to deal with pesky ascii errors in python 2.x
import sys
reload(sys)
sys.setdefaultencoding("utf8")

#Change this to CSV writer
def saveSubmission(submission, filename):
    if not submission.author:
        name = '[deleted]'
    else:
        name = submission.author.name
    csvwriter = csv.writer(open(filename, "a"))
    csvwriter.writerow([submission.created, submission.permalink,  name, submission.title, submission.selftext, submission.score])

# Downloads all the self posts from given subreddit
# ts_interval - the interval in seconds for each request cycle
# largest_timestamp - if not set, is set to 12 hours from now.
def getThreads(subredditName, ts_interval, ep1, ep2, user_ag, userAccount):
    filename = subredditName+'.csv'
    reddit = praw.Reddit(client_id='#$#$#$#',client_secret='#$#$#$#',user_agent=user_ag,password='#$#$#$#',username=userAccount)
    print(reddit.user.me())
    #If no time epoch is specified, 
    if ep2 is None:
        ep2 = int(time.time()) + 12*3600
    cts2 = ep2
    cts1 = ep2 - ts_interval
    currentTSInterval = ts_interval
    while True:
        try:
            searchResults = list(reddit.subreddit(subredditName).search('timestamp:{}..{}'.format(cts1, cts2), syntax='cloudsearch'))
        except Exception as e:
            #logging.exception(e)
            continue

        #logging.debug("Got {} submissions in interval {}..{}".format(len(searchResults), cts1, cts2))
        if len(searchResults) == 100:
            currentTSInterval /= 2
            cts1 = cts2 - currentTSInterval
           # logging.debug("Reducing time interval to {}".format(currentTSInterval))
            continue

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
    epc = int(time.time()) + 12*3600
    epb = int(time.time()) - 12*3600
    parser = argparse.ArgumentParser(description='Parallel Subreddit Downloader')
    parser.add_argument("--subreddit", dest="subreddit", required=True, help="Download the whole subreddit")
    parser.add_argument("--timestamp_interval", dest="timestamp_interval", type=int, required=True)
    parser.add_argument("--year", dest="collect_year", type=int, required=True)
    argsx = parser.parse_args()
    collect_year = str(argsx.collect_year)
    #List of accounts, these all have the same password as defined in common_pass
    loa = ['btcdataset']

    #Timeframe between which to scrape
    tst1 = '01.01.'+collect_year+' 00:00:00'
    tst2 = '31.12.'+collect_year+' 23:59:59'
    pattern = '%d.%m.%Y %H:%M:%S'

    #Timezone definition, OS based
    os.environ['TZ'] = 'UTC'
    common_pass='#$#$#$#'

    #Convert time string to epoch 
    epoch1 = int(time.mktime(time.strptime(tst1, pattern)))
    epoch2 = int(time.mktime(time.strptime(tst2, pattern)))

    #Increment
    inc = (epoch2 - epoch1 + 1)/8
    ep1 = [0]*8
    ep2 = [0]*8
    processes = []
    for i in range(0, 8):
        ep1[i] = epoch1 + i*inc
        ep2[i] = epoch1 + (i + 1)*inc - 1
        user_agx = 'mavvrr' + str(i)
        user = loa[0]
        p = Process(target=getThreads, args=(argsx.subreddit, argsx.timestamp_interval, ep1[i], ep2[i], user_agx, user))
        p.start()
        processes.append(p)

if __name__ == "__main__":
	start = time.time()
	main()
	end = time.time()
	print end - start
	
