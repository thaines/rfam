#! /usr/bin/env python3

import time
import random
import json

from urllib.parse import urljoin

from browser import Browser



# Specify how many of each asset type to create...
create = {
          'mat' : 50,
	        'prop' : 100,
	        'set' : 6,
	        'char' : 6,
	        'ani' : 12,
	        'shot' : 40,
	        'comp' : 40,
	        'video' : 2
				 }



# Directory to create each asset type in...
directory = {
	           'mat' : 'materials',
	           'prop' : 'props',
	           'set' : 'sets',
	           'char' : 'characters',
	           'ani' : 'animations',
	           'shot' : 'shots',
	           'comp' : 'composites',
	           'video' : 'final'
				    }



# Generate a random sequence of asset names, suitably long, to use above...
parts_a = ['giant', 'puny', 'ugly', 'purple', 'angry', 'hyper', 'spotted', 'lesser', 'tentacled', 'flying', 'dead', 'rainbow', 'spider', 'stone', 'antique']
parts_b = ['toad', 'unicorn', 'bear', 'shark', 'human', 'parrot', 'statue', 'tree', 'rock', 'horse', 'orc', 'butterfly', 'sheep', 'book', 'kettle', 'onion', 'cat', 'tree', 'waterfall', 'lake', 'hovercraft', 'zombie', 'park']

names = []
for pa in parts_a:
	for pb in parts_b:
		names.append(pa + ' ' + pb)

random.shuffle(names)



# Create a list of assets to create, and randomise the order...
to_create = []
for key, value in create.items():
	for _ in range(value):
		to_create.append(key)

random.shuffle(names)



# Load the target information and setup a simulated web browser...
f = open('target.json', 'r')
target = json.load(f)
f.close()

browser = Browser()



# Login...
user = browser.login(target)
print('Logged in with user %s' % user)



# Loop and process each asset in turn...
start = time.time()
times = []

for i, kind in enumerate(to_create):
	inner_start = time.time()
	
	# Open assets page...
	browser.open(urljoin(target['url'], 'assets'))
	
	# Open new asset page...
	browser.open(urljoin(target['url'], 'new'))
	
	# Create asset...
	browser.getJSON(urljoin(target['url'], 'add/asset'), {'name':names[i], 'type':kind, 'filename':directory[kind] +'/' + names[i] + '.blend', 'description':''})
	
	# Time stuff...
	inner_end = time.time()
	times.append(inner_end - inner_start)

end = time.time()



# Print out statistics...
print('Created %i assets' % len(to_create))
print('Added assets at %.1f per second.' % (len(to_create) / (end - start)))
print('Longest asset took %.2f seconds' % max(times))
print('First 64 assets took %.2f second' % sum(times[:64]))
print('Last 64 assets took %.2f second' % sum(times[-64:]))