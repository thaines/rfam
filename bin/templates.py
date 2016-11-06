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

import os
import os.path

from collections import Mapping
from collections import namedtuple



class PrefixDict(Mapping):
  """An overridden dictionary that feeds from multiple dictionaries depending on the key prefix, allowing normal keys and language translation keys to be combined."""
  def __init__(self, dicts):
    """Provided with a dictionary from prefix to dictionary to get from. No prefix is represented with the empty string key."""
    self.dicts = dicts
    
  def __getitem__(self, key):
    parts = key.split(':',1)
    if len(parts)==1:
      base = ''
      key = parts[0]
    else:
      base = parts[0]
      key = parts[1]
    
    if base not in self.dicts: return ''
    if key not in self.dicts[base]: return ''
    return self.dicts[base][key]

  def __iter__(self):
    for prefix, dic in self.dicts.iteritems():
      if prefix=='':
        for key in dic:
          yield key
      else:
        for key in dic:
          yield prefix + ':' + key
  
  def __len__(self):
    return sum(map(lambda d: len(d), self.dicts.values()))

  

class Templates:
  """Class that handles the templating system - loads all the templates and lets ypou return the results of running a template with a dictionary of parameters to control its behaviour. Templates are just html files in the templates directory that use dictionary string replacement notation (e.g. %(title)s) and have a hierarchy - the file main:base.html is filled in and then put into the %(inner)s variable of base.html (This can occur recursivly)"""
  def __init__(self, directory, language_func):
    """directory is where to find the templates, language_func is a function that returns a language dictionary - takes the current user as a parameter if defined."""
    files = [fn for fn in os.listdir(directory) if fn[-5:]=='.html']
    
    self.template = namedtuple('Template', ['data', 'parent'])
    self.templates = dict()
    
    for fn in files:
      # Read in the templates data...
      f = open(os.path.join(directory, fn), 'r')
      data = f.read()
      f.close()
      
      # Infer its name and parent...
      naked = fn[:-5] # Cull the .html
      if ':' in naked:
        name, parent = naked.split(':', 1)
      else:
        name = naked
        parent = None
      
      # Record it...
      self.templates[name] = self.template(data, parent)
    
    # Record the function that returns the language dictionary...
    self.language_func = language_func
 
  
  def __call__(self, name, dic, response):
    """name is the name of the template to run, dic the parameters to pass in to it - it returns the resulting string. Note that inner is a reserved keyword for dic, and typically should not be used; after running you may find that dic has been editted and now contains an 'inner' key. response is the response object - allows the tmeplates to obtain session info."""
    ret = None
    
    language = self.language_func(response.user) if hasattr(response, 'user') else self.language_func()
    dic_lang = PrefixDict({"" : dic, "text" : language, "session" : response.__dict__})
    
    while name!=None:
      template = self.templates[name]
      if ret!=None: dic['inner'] = ret
      ret = template.data % dic_lang
      name = template.parent
    
    return ret
