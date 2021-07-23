# Copyright 2014 Tom SF Haines

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import io
import sys
import urllib.parse
import datetime
import json



class Response:
  """Simple class to handle the response from a web request. Also provides access to the environment via various conveniance functions. Does a bunch of things automatically, such as providing content length."""
  def __init__(self, environ):
    self.env = environ
    
    self.code = '200 OK'
    self.head = dict()
    self.data = []
    self.length = 0 # Of the above, all concatenated together.
    self.f = None # A file that can be returned, in its entirity. Closed after use.
    
    self.path = None
    self.cookie = None
    self.query = None
  
  
  def log(self):
    """Returns a stream that stuff can be logged to, for error reporting."""
    return self.env['wsgi.errors']


  def getPath(self):
    """Returns the path of the call, as a list of terms"""
    if self.path==None:
      self.path = self.env['PATH_INFO'].rstrip('/').strip('/').split('/')
    return self.path
  
  
  def getCookie(self):
    """Returns a dictionary of whatever is in the cookie; if no cookie then empty dictionary."""
    if self.cookie==None:
      self.cookie = dict()
      if 'HTTP_COOKIE' in self.env:
        for pair in self.env['HTTP_COOKIE'].split(';'):
          key, value = pair.split('=', 1)
          self.cookie[key.strip()] = value.strip()
    return self.cookie
  
  
  def getQuery(self):
    """Returns a dictionary of the query string parameters."""
    if self.query==None:
      self.query = dict()
      try:
        for key, value in urllib.parse.parse_qsl(self.env['QUERY_STRING'], True, True):
          self.query[key] = value
      except ValueError:
        pass
    return self.query
  
  
  def getJsonPost(self):
    """Returns an object extracted from json that has been posted, returns None if there was no post."""
    # Get length of content...
    try:
      length = int(self.env.get('CONTENT_LENGTH', '0'))
    except ValueError:
      length = 0
    
    # If length==0 then return None...
    if length==0:
      return None
    
    # Get body and try and interpret is json...
    body = self.env['wsgi.input'].read(length)
    return json.loads(body.decode('utf-8'))
  
  
  def make404(self):
    """Fills it in as a 404."""
    self.code = '404 NOT FOUND'
    self.head = {'Content-type' : 'text/plain'}
    self.data = [b'404 - Not found; your URL has been fed to the friendly neighborhood grue']
    self.length = len(self.data[0])
    self.f = None
  
  
  def make403(self):
    """Fills it in as a 403."""
    self.code = '403 FORBIDDEN'
    self.head = {'Content-type' : 'text/plain'}
    self.data = [b'403 - Access denied; fortunatly for you the friendly neighbourhood grue is on a diet']
    self.length = len(self.data[0])
    self.f = None
  
  
  def make418(self):
    """Fills it in as a 418."""
    self.code = "418 I'M A TEAPOT"
    self.head = {'Content-type' : 'text/plain'}
    self.data = [b'418 - Due to the extensive use of improbability drives in this galactic neighbourhood at the precise moment you made the request the server was a teapot.']
    self.length = len(self.data[0])
    self.f = None
  
  
  def make500(self):
    """Fills it in as a 418."""
    self.code = '500 INTERNAL SERVER ERROR'
    self.head = {'Content-type' : 'text/plain'}
    self.data = [b'500 - Internal server error. Sorry about that.']
    self.length = len(self.data[0])
    self.f = None
  
  
  def refresh(self):
    to = self.env['PATH_INFO']
    print('refresh', to)
    self.code = '303 REFRESH'
    self.head = {'Content-type' : 'text/plain',
                 'Location' : to}
    self.data = [b'303 - refresh page']
    self.length = len(self.data[0])
    self.f = None
    
  
  def setPlain(self):
    """Sets the content type to indicate that the return is plain text."""
    self.head['Content-type'] = 'text/plain'
  
  
  def setHTML(self):
    """Sets the content type to indicate that the return is html."""
    self.head['Content-type'] = 'text/html'
  
  
  def setJavascript(self):
    """Sets the content type to indicate that the return is javascript."""
    self.head['Content-type'] = 'application/javascript'
  
  
  def setJSON(self):
    """Sets the content type to indicate that the return is json data."""
    self.head['Content-type'] = 'text/json'
  
  
  def setCSS(self):
    """Sets the content type to indicate that the return is css."""
    self.head['Content-type'] = 'text/css'
  
  
  def setPNG(self):
    """Sets the content type to indicate that the return is a png file."""
    self.head['Content-type'] = 'image/png'
  
  
  def setJPEG(self):
    """Sets the content type to indicate that the return is a jpeg file."""
    self.head['Content-type'] = 'image/jpeg'
  
  
  def allowCache(self, seconds = 3600):
    """If called updates the header to allow caching of this asset."""
    self.head['Cache-control'] = 'max-age=%i, public' % seconds
  
  
  def addCookie(self, key, value, timeout = 24):
    """Allows you to set a cookie key-value for this website; call repeatedly for multiple key/value pairs. The optional timeout parameter is given in hours."""
    if 'Set-Cookie' not in self.head:
      self.head['Set-Cookie'] = []
    
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=timeout)
    
    cookie = '%s=%s' % (key, value)
    cookie += '; Expire=%s;'%expire.strftime('%a, %d-%b-%Y %H:%M:%S UTC')
    cookie += ' Path=/; HttpOnly'
    
    self.head['Set-Cookie'].append(cookie)

  
  def append(self, text):
    """Allows you to add more content to the response head - you feed it a string."""
    data = bytes(text, 'utf8')
    self.length += len(data)
    self.data.append(data)
  
  
  def provideFile(self, f):
    """Allows you to add a file to the object - it takes ownership and will close the file when its done with it. The cursor position when handed it over is taken as the start, going all the way until the end of the file."""
    if self.f!=None:
      self.f.close()
    self.f = f

  
  def header(self):
    """Iterates the lines from the current header"""
    for key, value in self.head.items():
      if isinstance(value, list):
        for val in value:
          yield (key, val)
      else:
        yield key, value
  
  
  def response(self, start_response):
    """Given the start_response of a WSGI application this calls it with the headers and returns the correct return to then be returned from a WSGI application. After calling this this object should be considered unsafe, and left to the grabage collector."""
    if self.f!=None:
      # We have a file to provide - this is going to get fiddly...
      l = self.length
      sp = self.f.tell()
      self.f.seek(0, io.SEEK_END)
      l += self.f.tell() - sp
      self.f.seek(sp, io.SEEK_SET)
      
      self.head['Content-length'] = str(l)
      start_response(self.code, list(self.header()))
      
      def mundivore(data, f):
        for d in data:
          yield d

        while True:
          d = f.read(1024)
          if len(d)==0: break
          yield d
        
        f.close()
        
      return mundivore(self.data, self.f)
    
    else:
      # Straight return of in-memory data...
      self.head['Content-length'] = str(self.length)
      start_response(self.code, list(self.header()))
      
      return self.data
