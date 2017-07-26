#import scrapy
import urllib2
import json

#importing sys to take command line arguments
import sys

#string to unix timestamp formatting 
import time 
import datetime
from dateutil.parser import parse as dateparser

#literal evaluation, convert string to dict (getAuthor)
import ast
from dateutil.parser import parse as dateparse
from bs4 import BeautifulSoup

import csv 

#Setting default to UTF8 to deal with pesky ascii errors in python 2.x
import sys;
reload(sys);
sys.setdefaultencoding("utf8")

cmdargs = sys.argv
#list available irc channels 
ircchannels = ['otc','dev']

#Prevent errors straight up. Just dont allow anything that doesnt exist 
availableyears = ['2011','2012','2013','2014','2015','2016','2017']

print cmdargs[2]
#if selected irc channel is valid, set it, otherwise terminate 
if str(cmdargs[1]) in ircchannels:
	scrape_channel =  str(cmdargs[1])
else:
	sys.exit('The specified IRC channel is not valid. Select otc or dev')

#if selected year is valid go ahead and set it, otherwise terminate
if str(cmdargs[2]) in availableyears:
	scrape_year = str(cmdargs[2])
else:
	sys.exit('The specified year is not valid. Data available from 2011 to 2017')


#Initialize empty array storing all messages
all_messages = []

#Initialize filename for message storage. 
filename = 'bitcoin-#'+scrape_channel+'-'+scrape_year+str(int(time.time()))+'.csv'
#Loop over every month
for i in range(1,13):

	#Create URL for each month. Zfill to add 0 prefix to integers < 10 (02, 03, etc.)
	month_url = "http://bitcoinstats.com/irc/bitcoin-"+scrape_channel+"/logs/"+scrape_year+"/"+str(i).zfill(2)+"/"

	#loop over every day in the month. Opening these gets the actual chat logs 
	for j in range (1,32):
		
		#Same as for months, also zfill
		day_url = month_url+str(j).zfill(2)

		#set header to prevent access denied
		hdr = {'Accept': 'text/html,application/xhtml+xml,*/*',"user-agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36"}
		
		#in case of 404/url read error continue to next URL
		try:
			req = urllib2.Request(day_url,headers=hdr)
			html_string = urllib2.urlopen(req).read()
		except: 
			break

		#BeautifulSoup parser for quick selection of elements 
		html = BeautifulSoup(html_string)
		day = j
		month = i

		#cli argument is string by default, convert it to int 
		year = int(scrape_year)
		rows = html.find_all('tr')
		for row in rows:
			username = row.find('td', {'class':'nickname'}).text
			irc_time = row.find('td', {'class':'datetime'}).text
			hours = int(irc_time.split(":")[0])
			minutes = int(irc_time.split(":")[1])

			#Just setting seconds to 0, not recorded in IRC archive... 
			seconds = 00

			#Convert timestamp to datetime object. Doing this for all scrapers, so consistnecy.. 
			timestamp = datetime.datetime(year, month, day, hours, minutes,seconds)
			text = row.find('td', {'class':None}).text 
			message = [timestamp,username,text]
			print message
			all_messages.append(message)

			#write the entire thing to a CSV 
			with open(filename, "a") as f:
			    writer = csv.writer(f)
			    writer.writerow(message)



