#! /usr/bin/env python3

import time
import random
import json

from urllib.parse import urljoin
from html.parser import HTMLParser

from browser import Browser



# Script to randomly browse the target, loading random webpages to see what is happening...


# Load the target information and setup a simulated web browser...
f = open('target.json', 'r')
target = json.load(f)
f.close()

browser = Browser()



# Login...
user = browser.login(target)
print('Logged in with user %s' % user)



# Find a list of top level pages...
class FindPages(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.pages = []
		self.collect_next = False
	
	def handle_starttag(self, tag, attrs):
		if tag=='div':
			if self.collect_next:
				self.collect_next = False
				for key, value in attrs:
					if key=='id':
						self.pages.append(value[5:])
			
			else:
				for key, value in attrs:
					if key=='class' and value=='header_tab':
						self.collect_next = True

parser = FindPages()
parser.feed(browser.current())
pages = parser.pages
del parser

print('Found pages:')
print('; '.join(pages))



# Hammer time...
try:
	while True:
		# Time loading a lot of pages...
		count = 128
		start = time.time()
	
		for _ in range(count):
			page = random.choice(pages)
			browser.open(urljoin(target['url'], page))
	
		end = time.time()
	
		# Report speed...
		print('>> Loading top level pages at %.1f per second (Ctrl-C to stop)' % (count / (end - start)))

except KeyboardInterrupt:
	print('Done.')
