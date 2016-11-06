#! /usr/bin/env python3

import time
import json

from urllib.parse import urljoin

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



# Load the assets page a bunch of times...
count = 64
start = time.time()

for _ in range(count):
	browser.open(urljoin(target['url'], 'assets'))

end = time.time()



# Print out how many times the assets page can be loaded per second...
print('Assets page loads %.2f times per second' % (count / (end - start)))
