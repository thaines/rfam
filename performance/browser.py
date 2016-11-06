import random
import json

import urllib
from urllib.parse import urljoin, urlencode
from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor

from html.parser import HTMLParser



class ReadPage(HTMLParser):
	"""For internal use by Browser only."""
	def __init__(self, browser):
		HTMLParser.__init__(self)
		self.browser = browser
		
	def handle_starttag(self, tag, attrs):
		if tag=='script':
			for key, value in attrs:
				if key=='src':
					self.browser.open_more(value)
		
		if tag=='link':
			for key, value in attrs:
				if key=='href':
					self.browser.open_more(value)
		
		if tag=='img':
			for key, value in attrs:
				if key=='src':
					self.browser.open_more(value)



class FindUsers(HTMLParser):
	def __init__(self, project):
		HTMLParser.__init__(self)
		self.project = project
		self.users = []
	
	def handle_starttag(self, tag, attrs):
		if tag=='div':
			ats = dict()
			for key, value in attrs:
				ats[key] = value
			
			if 'class' in ats and ats['class']=='user':
				if self.project in eval(ats['data-projects']):
					self.users.append(ats['data-ident'])



class Browser:
	"""Simple wrapper around bunch of python modules that fully loads a webpage, for realistic load. Ignores caching, so is heavier than a normal web browser."""
	def __init__(self):
		self.jar = CookieJar()
		self.opener = build_opener(HTTPCookieProcessor(self.jar))
	
	
	
	def open(self, url):
		"""Reads the url, raising an error if something goes wrong."""
		self.data = dict()
		self.url = url
		
		response = self.opener.open(url)
		self.data[url] = response.read().decode('utf-8')
		
		parser = ReadPage(self)
		parser.feed(self.data[url])
	
	
	def current(self):
		return self.data[self.url]
	
	
	def open_more(self, url):
		url = urljoin(self.url, url)
		
		response = self.opener.open(url)
		self.data[url] = response.read()
	
	
	def getJSON(self, url, payload):
		"""Equivalent to the same in jQuery."""
		data = urlencode(payload)
		response = self.opener.open(url + '?' + data)
		return json.loads(response.read().decode('utf-8'))
	
	
	def users_by_project(self, project):
		"""If you have just open the rfam login page this will return a list of all users that are associated with the given project."""
		parser = FindUsers(project)
		parser.feed(self.data[self.url])
		return parser.users
	
	
	def login(self, target):
		"""Will login to the 3Dami server given the configuration dictionary so it knows the target url and project to login to."""
		self.open(target['url'])
		user = random.choice(self.users_by_project(target['project']))

		response = self.getJSON(urljoin(target['url'], 'login'), {'project' : target['project'], 'user' : user})

		self.open(target['url'])
		
		return user
