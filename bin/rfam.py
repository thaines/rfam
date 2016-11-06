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
import json
import time
import datetime
import logging

import xml.sax.saxutils as saxutils

from .templates import Templates
from .fs_db import FSDB
from .fs_db_json import JsonFileType

from .jobs import Jobs



class RFAM:
  """Represents the state of the server, used for multiple connections, though designed so that if many of them are running at once nothing bad will happen. Effectivly the interface between the client requests and the actual state; its main purpose is to cache loads of json files."""
  def __init__(self):
    # Load the main configuration file...
    f = open('config.json', 'r')
    self.config = json.loads(f.read())
    f.close()
    
    # Load the paths, so we can find all the data...
    self.paths = dict()
    for fn in os.listdir(self.config['paths']):
      if fn.endswith('.json'):
        f = open(os.path.join(self.config['paths'], fn), 'r')
        path = json.loads(f.read())
        f.close()
        
        self.paths[path['ident']] = path['path']
    
    # Use it to prepare the other fsdb databases for the projects and users directories, include a timer so we don't query these databases too often...
    self.projects = FSDB(self.config['projects'], self.config['single_proc'])
    self.projects.register(JsonFileType())
    
    self.users = FSDB(self.config['users'], self.config['single_proc'])
    self.users.register(JsonFileType())

    # Record a last refreshed time, so it knows when to check for user/project datastore changes...
    self.ident_to_project = {}
    self.last_refresh = time.time() - self.config['cache']
        
    # We load language dictionaries as needed...
    self.languages = dict()
    
    # Initialise the templates system...
    self.templates = Templates(self.config['templates'], self.getLanguage)
    
    # The file system 'databases' for each project - this is where the magic occurs...
    self.dbs = dict()
    
    # The defaults used by projects when creating files, and other stuff...
    self.dbs_defaults = dict()
    
    # Job queue used for the render farm...
    self.jobs = Jobs(self)
    
    # Setup logging...
    if 'log' in self.config:
      fn = self.config['log'] % {'pid' : str(os.getpid())}
      try:
        os.makedirs(os.path.dirname(fn))
      except:
        pass
      
      form = '%(asctime)s | %(message)s'
      logging.basicConfig(filename=fn, level=logging.DEBUG, format=form)


  def development(self):
    """Returns True in development mode, false for real use - some code queries it to decide how cachy/fast etc. to be."""
    return False
  
  
  def log(self, response, message):
    """Logs the given message, noting that it adds user and project from response of avaliable."""
    
    user = response.user if response.user!=None else ''
    project = response.project if response.project!=None else ''
    
    logging.info("(%s,%s) | %s" % (user, project, message))

  
  def real(self, path):
    """Converts from a path that is in terms of the registered paths to a real operating system path."""
    head, tail = path.split('::', 1)
    return os.path.join(self.paths[head], tail)
  
  
  def getLogoPath(self):
    """Returns the path to the logo"""
    return self.config['logo']


  def getIconPath(self):
    """Returns the path to the icon"""
    return self.config['icon']


  def getJavascriptPath(self):
    """Returns the path to the javascript."""
    return self.config['javascript']
  
  
  def getStylesheetsPath(self):
    """Returns the path where we can find the stylesheets."""
    return self.config['stylesheets']


  def getLanguage(self, user = None):
    """Returns the language translation dictionary, in the language of the given user. If None then it uses the global default."""
    if user==None:
      language = self.config['language']
    else:
      language = self.ident_to_user[user]['language']
    
    if language not in self.languages:
      f = open(os.path.join(self.config['languages'],language + '.json'), 'r')
      self.languages[language] = json.loads(f.read())
      f.close()
      
    return self.languages[language]
    
  
  def __refresh(self):
    """We rebuild indices as needed - don't want to do so too often as it gets expensive."""
    now = time.time()
    if now >= (self.last_refresh + self.config['cache']):
      self.last_refresh = now
      
      prev = self.ident_to_project
      self.ident_to_project = dict()
      projects = self.projects.get_root()
      for project in projects:
        if project.endswith('.json'):
          project = projects[project].read()
          self.ident_to_project[project['ident']] = project
          
          if project['ident'] in prev:
            if prev[project['ident']]['directory'] != project['directory']:
              del self.dbs[project['ident']]
            
            if prev[project['ident']]['default'] != project['default']:
              del self.dbs_defaults[project['ident']]
          
            del prev[project['ident']]
      
      for key in prev.keys():
        if key in self.dbs: del self.dbs[key]
        if key in self.dbs_defaults: del self.dbs_defaults[key]
    
      self.ident_to_user = dict()
      users = self.users.get_root()
      for user in users:
        if user.endswith('.json'):
          user = users[user].read()
          self.ident_to_user[user['ident']] = user


  def getProjects(self):
    """Returns a list of all project identifiers."""
    self.__refresh()
    return self.ident_to_project.keys()
  
  
  def getProject(self, ident):
    """Given the identifier for a project returns a dictionary of information about that project. Do not edit."""
    self.__refresh()
    if ident in self.ident_to_project:
      return self.ident_to_project[ident]
    else:
      return None
  
  
  def proj(self, ident):
    """Given the identifier of a project this returns a FSDB object representing it - it is through this that all data access occurs."""
    self.__refresh()
    if ident not in self.dbs:
      p = self.getProject(ident)
      path = self.real(p['directory'])
      
      if not os.path.exists(path):
        os.makedirs(path)
      
      self.dbs[ident] = FSDB(path, self.config['single_proc'])
      self.dbs[ident].register(JsonFileType())
    
    return self.dbs[ident]
  
  
  def proj_defaults(self, ident):
    """Given the identifier of a project this returns a FSDB object for its defaults directory - this is the configuration information that gives details like types, states and priorities."""
    self.__refresh()
    if ident not in self.dbs_defaults:
      p = self.getProject(ident)
      path = self.real(p['default'])
      
      self.dbs_defaults[ident] = FSDB(path, self.config['single_proc'])
      self.dbs_defaults[ident].register(JsonFileType())
    
    return self.dbs_defaults[ident]


  def getUsers(self):
    """Returns a list of all user identifiers."""
    self.__refresh()
    return self.ident_to_user.keys()
  
  
  def getUser(self, ident):
    """Given the identifier for a user returns a dictionary of information about that user. Do not edit."""
    self.__refresh()
    if ident in self.ident_to_user:
      return self.ident_to_user[ident]
    else:
      return None
  
  
  def getUsersByProject(self, ident):
    """Returns a list of all users on the given project."""
    self.__refresh()
    
    def on_proj(user):
      return ident in self.ident_to_user[user]['projects']
      
    return list(filter(on_proj, self.ident_to_user.keys()))
  
  
  def template(self, name, dic, response):
    """Given the name of a template and a dictionary of parameters to use when filling it in this returns the resultant string. Also provide the current response, so the templates can get session data."""
    return self.templates(name, dic, response)
  
  
  def types(self, project):
    """Returns a list of type identifiers for the given project."""
    ddb = self.proj_defaults(project)
    
    ret = []
    for child in filter(lambda n: n.endswith('.json'), ddb['asset_types']):
      targ = ddb['asset_types', child].read()
      ret.append(targ['ident'])
      
    return ret
  
  
  def getType(self, project, ident):
    """Given the identifier of a type returns its type data structure (A dictionary loaded form the related json file.), or None if not recognised."""
    ddb = self.proj_defaults(project)
    
    for child in filter(lambda n: n.endswith('.json'), ddb['asset_types']):
      targ = ddb['asset_types', child].read()
    
      if targ['ident']==ident:
        return targ

    return None


  def getState(self, project, ident):
    """Given the identifier of a state returns its data structure (A dictionary loaded form the related json file.), or None if not recognised."""
    ddb = self.proj_defaults(project)
    
    for child in filter(lambda n: n.endswith('.json'), ddb['states']):
      targ = ddb['states', child].read()
    
      if targ['ident']==ident:
        return targ

    return None
  
  
  def typeChoice(self, project, selected = None):
    """Returns a string that can be dumped into a select statement - basically a list of asset types that are valid for the given project. You can optionally provide a type ident to be selected by default"""
    ddb = self.proj_defaults(project)
    
    ret = []
    for child in filter(lambda n: n.endswith('.json'), ddb['asset_types']):
      at = ddb['asset_types', child].read()
      sel = 'selected' if selected==at['ident'] else ''
      ext = ('.' + at['file'].split('.')[-1]) if 'file' in at else ''
    
      ret.append((at['sort'], '<option %s data-dir="%s" data-ext="%s" value="%s">%s</option>' % (sel, at['directory'], ext, at['ident'], saxutils.escape(at['name']))))
  
    ret = ''.join(map(lambda c: c[1], sorted(ret)))
    return ret


  def userChoice(self, project, selected = None, inc_unowned = False, user = None):
    """Returns a string that can be dumped into a select statement - basically a list of choices for all the users on the given project. You can optionally provide a user ident to be selected by default, and if you set inc_unowned to True you get an 'Unowned' entry in the list, which will be selected by default if selected is set to None."""
    def make_option(ident):
      user = self.getUser(ident)
      sel = 'selected' if selected==ident else ''
      return '<option %s value="%s">%s</option>' % (sel, ident, saxutils.escape(user['name']))
    
    users = self.getUsersByProject(project)
    lines = map(make_option, users)
    
    if inc_unowned:
      line = '<option value="">%s</option>' % self.getLanguage(user)['unowned']
      lines = [line] + list(lines)
    
    return ''.join(lines)
  
  
  def stateChoice(self, project, at, selected):
    """Returns a string to go in a select html element of the states for an asset - you need to provide the project, and the asset type as they both influence the list, as well as which one is selected."""
    
    # Obtain the type object of the provided ident, use it to create an output list...
    at = self.getType(project, at)
    ret = [None] * len(at['states'])
    
    # Iterate the states and insert them in their correct positions...
    ddb = self.proj_defaults(project)
    for name in filter(lambda n: n.endswith('.json'), ddb['states']):
      state = ddb['states', name].read()
      try:
        pos = at['states'].index(state['ident'])
        sel = 'selected' if selected==state['ident'] else ''
        ret[pos] = '<option %s value="%s">%s</option>' % (sel, state['ident'], saxutils.escape(state['name']))
      
      except ValueError:
        pass # State not supported by this type.
    
    # Return it...
    return ''.join(ret)
    
    
  def priorityInterface(self, project, value):
    """Returns a html element string for the priority selection of an asset - will either be an input or select depending on the configuration options of the project."""
    config = self.proj_defaults(project)['priority.json'].read()
    if 'names' in config and isinstance(config['names'], list):
      # Dropdown dialog of choices...
      low = config['low']
      high = config['high']
      names = config['names']
      selected = int((len(names) -1) * ((value-low) / float(high-low)) + 0.5)
      
      ret = []
      div = len(names) - 1.0
      for pos, name in enumerate(names):
        val = int(low + (high-low) * (pos / div))
        sel = 'selected' if pos==selected else ''
        ret.append('<option %s value="%i">%s</option>' % (sel, val, name))
      
      return '<select>' + ''.join(ret) + '</select>'
    
    else:
      # Numeric input...
      return '<input data-min="%i" data-max="%i" type="number" value="%i">' % (low, high, value)
  
  
  def format_render_time(self, user, asset):
    """Given the information about an asset this formats and returns a string representing the render time information."""
    if 'render_time' not in asset:
      return self.getLanguage(user)['render_time:none']
    
    elif 'video' in asset['render_time']:
      rt = asset['render_time']
      time = datetime.timedelta(seconds=int(rt['video'][-1]))
      return self.getLanguage(user)['render_time:video'] + str(time)
    
    else: # Normal render.
      rt = asset['render_time']
      
      # First pass - find the min, max average and range of frames...
      low_frame = None
      high_frame = None
      
      min_time = None
      min_frame = None
      max_time = None
      max_frame = None
      
      count = 0
      mean = 0.0
      
      for frame, times in rt.items():
        frame = int(frame)
        
        if low_frame==None or low_frame>frame:
          low_frame = frame
        if high_frame==None or high_frame<frame:
          high_frame = frame
        
        if min_time==None or min_time > times[-1]:
          min_time = times[-1]
          min_frame = frame
        if max_time==None or max_time < times[-1]:
          max_time = times[-1]
          max_frame = frame
        
        count += 1
        mean += (times[-1] - mean) / count
      
      # Record the information just calculated...
      ret = []
      
      time = datetime.timedelta(seconds=int(mean))
      ret.append(self.getLanguage(user)['render_time:mean'] + str(time))
      
      time = datetime.timedelta(seconds=int(min_time))
      ret.append(self.getLanguage(user)['render_time:min'] + str(time) + ' (%i)' % min_frame)
      
      time = datetime.timedelta(seconds=int(max_time))
      ret.append(self.getLanguage(user)['render_time:max'] + str(time) + ' (%i)' % max_frame)
      
      # Second pass to get predicted render time...
      guessed = False
      total_low = 0.0
      total_mean = 0.0
      total_high = 0.0
      
      for frame in range(low_frame, high_frame+1):
        if str(frame) in rt:
          val = rt[str(frame)][-1]
          total_low += val
          total_mean += val
          total_high += val
        else:
          total_low += min_time
          total_mean += mean
          total_high += max_time
          guessed = True
      
      # Record the (estimated) total times...
      time = datetime.timedelta(seconds=int(total_mean))
      ret.append(self.getLanguage(user)['render_time:estimate'] + str(time))
        
      if guessed:
        time = datetime.timedelta(seconds=int(total_low))
        ret.append(self.getLanguage(user)['render_time:estimate:min'] + str(time))
        
        time = datetime.timedelta(seconds=int(total_high))
        ret.append(self.getLanguage(user)['render_time:estimate:max'] + str(time))
      
      # Build and return the information string...
      return self.getLanguage(user)['render_time:div'].join(ret)
