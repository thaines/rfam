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
import time
import datetime
import math
import random

import json
import uuid

import subprocess
from urllib.request import urlopen

from worker import Worker



class Node:
  """Runs a set of workers, with code to handle all the waiting and server polling etc."""
  def __init__(self):
    # Load the configuration...
    f = open('config.json', 'r')
    self.config = json.loads(f.read())
    f.close()
    
    # Load the paths...
    self.paths = {}
    
    for fn in os.listdir(self.config['paths']):
      if fn.endswith('.json'):
        f = open(os.path.join(self.config['paths'], fn), 'r')
        path = json.loads(f.read())
        f.close()
        
        self.paths[path['ident']] = path['path']
    
    # Setup the heartbeat value - None means we don't yet know it (ask the server...)...
    self.last_info = 0.0 # Offset from unix epoc, so will update immediatly.
    self.heartbeat = 4.0
    self.arrhythmia = 1.0
    self.error_scale = 2.0
    self.hibernation = 600.0
    self.memory = 600.0
    
    self.errors = 0 # Number of errors in a sequence at this point.
    
    # Handle the location of blender...
    self.blender = os.path.abspath(os.path.expanduser(self.config['blender']))
    
    # Prepare the name...
    self.name = self.config['name']
    if self.name==None:
      self.name = uuid.uuid1().hex
    
    self.must_send = [] # Messages that must be sent - kept for when a connection error appears.
    
    # Create the workers...
    self.workers = [Worker(self, c) for c in self.config['processes']]
    
    self.first_hello = True
  
  
  def to_local(self, path):
    """Converts a path provided by the server to a local path."""
    head, tail = path.split('::', 1)
    return os.path.join(self.paths[head], tail)

  
  def hello(self):
    """Says hello to the server, correctly handling the commands etc. Returns a list of processes that we are waiting on to do work, which can be empty. Will return None if something went wrong."""
    
    # Create the package to be sent to the server...
    requests = self.must_send[:]
    
    requests.append({'id' : 'identity', 'name' : self.name, 'provides' : self.config['provides']})
    if 'version' in self.config:
      requests[0]['version'] = self.config['version']
    
    too_old = time.time() - self.memory
    if self.last_info < too_old:
      requests.append({'id' : 'info'})
    
    lazy_workers = []
    for worker in self.workers:
      r = worker.state()
      if r!=None:
        requests.append(r)
        if r['id']=='done':
          print(datetime.datetime.utcnow().isoformat(' '), ':: Rendered frame %s of %s in %.1f seconds' % (str(worker.frame), worker.fn, r['time']))
          self.must_send.append(r)
      
      if not worker.busy():
        lazy_workers.append(worker)
    
    if len(lazy_workers)!=0 and (self.first_hello or self.config['single_use']==False):
      self.first_hello = False
      print(datetime.datetime.utcnow().isoformat(' '), ':: Requesting %i job(s)' % len(lazy_workers))
      requests.append({'id' : 'task', 'paths' : [p for p in self.paths.keys()], 'provides' : self.config['provides'], 'count' : len(lazy_workers)})
    
    # Send it to the server...
    try:
      req = urlopen('%s/farm'%self.config['server'], json.dumps(requests).encode('utf-8'))
    except IOError:
      # Problem - return as such...
      return None

    self.must_send = []
    
    # Parse the data...
    commandments = json.loads(req.read().decode('utf-8'))
    
    # Go through and handle the commandments...
    for commandment in commandments:
      if commandment['id']=='info':
        self.last_info = time.time()
        self.heartbeat = float(commandment['heartbeat'])
        self.arrhythmia = float(commandment['arrhythmia'])
        self.error_scale = float(commandment['error_scale'])
        self.hibernation = float(commandment['hibernation'])
        self.memory = float(commandment['memory'])
        print(datetime.datetime.utcnow().isoformat(' '), ':: Heartbeat set to %.1f seconds' % self.heartbeat)

      elif commandment['id']=='task':
        print(datetime.datetime.utcnow().isoformat(' '), ':: Render request for job %s' % commandment['uuid'])
        print('  File %s' % commandment['file'])
        print('  Frame %s' % commandment['frame'])
        
        worker = lazy_workers.pop()
        worker.run(commandment)
        
      elif commandment['id']=='kill':
        print(datetime.datetime.utcnow().isoformat(' '), ':: Kill request for task %s, frame %i' % (commandment['uuid'], commandment['frame']))
        for worker in self.workers:
          worker.kill(commandment)

      else:
        print(datetime.datetime.utcnow().isoformat(' '), ':: Unknown commandment:')
        print(commandment)
    
    # Get a list of processes we need to wait for to return...
    return [worker.p() for worker in self.workers if worker.busy()]


  def run(self):
    """Runs a full loop - call this to create a fully functioning Node."""
    if self.config['jitter'] > 1e-3:
      time.sleep(random.random() * self.config['jitter'])
    
    while True:
      # Say hello to the server...
      wait_on = self.hello()
      if wait_on==None:
        wait_on = []
        print(datetime.datetime.utcnow().isoformat(' '), ':: Error talking to server - will retry')
        self.errors += 1
      else:
        self.errors = 0
      
      # Work out a sleep time...
      hb = self.heartbeat
      if self.errors!=0:
        hb *= math.pow(self.error_scale, self.errors)
        if hb>self.hibernation:
          hb = self.hibernation
      
      hb += self.arrhythmia * random.random()
      
      # Sleep, either with wake on one of the processes ending or just sleep...
      if len(wait_on)==0:
        if self.config['single_use']: # In single use mode this basically means we are done.
          return
        
        time.sleep(hb)
        
      else:
        end = time.time() + hb
        tick = self.config['tick']
        
        while time.time() < end: # Could someone please tell me a better way of doing this:-/
          done = False
          for proc in wait_on:
            if proc.poll()!=None:
              done = True
              break
          if done:
            break
            
          time.sleep(tick)      
