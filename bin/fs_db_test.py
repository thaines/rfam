#! /usr/bin/env python3
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

import unittest
import tempfile

from . import fs_db
from . import fs_db_json



class TestFSDB(unittest.TestCase):
  """Unit tests of State object - create a temporary directory with a known structure and then verifies it behaves itself, including caching behaviour etc - will take a while as it has to wait for some timeouts."""
  def setUp(self):
    self.temp_dir = tempfile.TemporaryDirectory()
    self.root = self.temp_dir.name
    
    open(os.path.join(self.root, 'cabbage.txt'), 'w').close()
    open(os.path.join(self.root, 'turnip.txt'), 'w').close()
    
    os.mkdir(os.path.join(self.root, 'penguins'))
    open(os.path.join(self.root, 'penguins/fly.txt'), 'w').close()
    
    os.mkdir(os.path.join(self.root, '.lock_spiders.txt'))
  
  
  def tearDown(self):
    self.temp_dir.cleanup()
  
  
  def test_creation(self):
    """Verify that the object can be created and then deleted without issue."""
    s = fs_db.FSDB(self.root)
    
    self.assertTrue(s.get_root()==s[()])
    
    del s
  
  
  def test_len(self):
    """Verifies that the correct object count is returned, or that I can count - its one of them!"""
    s = fs_db.FSDB(self.root)
    
    self.assertTrue(len(s)==5)
    
    del s


  def test_get(self):
    """Does a bunch of gets and verifies that it gets the right results, via path."""
    s = fs_db.FSDB(self.root)
    
    self.assertTrue(s[()].path()==())
    self.assertTrue(s['cabbage.txt'].path()==('cabbage.txt',))
    self.assertTrue(s['penguins','fly.txt'].path()==('penguins','fly.txt'))
    
    with self.assertRaises(KeyError):
      _ = s[('lion.txt',)]
      
    with self.assertRaises(KeyError):
      _ = s['lion.txt']

    with self.assertRaises(KeyError):
      _ = s['penguins','dance.txt']

    with self.assertRaises(KeyError):
      _ = s['cabbage.txt','word_domination.txt']
      
    del s
  
  
  def test_contains(self):
    """Verify that contains is behaving itself."""
    s = fs_db.FSDB(self.root)
    
    self.assertTrue('cabbage.txt' in s)
    self.assertTrue(('cabbage.txt',) in s)
    self.assertTrue(('penguins', 'fly.txt') in s)
    
    self.assertTrue('cats.txt' not in s)
    self.assertTrue(('cabbage.txt', 'wibble.txt') not in s)
    self.assertTrue(('penguins', 'dance.txt') not in s)
    
    del s
  
  
  def test_iter(self):
    """Checks we get back the right stuff when iterating the FSDB object."""
    s = fs_db.FSDB(self.root)
    
    paths = []
    for path, node in s.items():
      self.assertTrue(path==node.path())
      paths.append(path)
    
    expected = {(), ('cabbage.txt',), ('turnip.txt',), ('penguins',), ('penguins', 'fly.txt')}
    self.assertTrue(set(paths)==expected)
    
    del s
    
  
  def test_node_isa(self):
    """Tests the is-a method of the Node object."""
    s = fs_db.FSDB(self.root)
    
    self.assertTrue(s[()].isa()==fs_db.Node.DIRECTORY)
    self.assertTrue(s['cabbage.txt'].isa()==fs_db.Node.FILE)
    self.assertTrue(s['penguins'].isa()==fs_db.Node.DIRECTORY)
    self.assertTrue(s['penguins','fly.txt'].isa()==fs_db.Node.FILE)
    
    del s
    
    
  def test_node_path(self):
    """Checks the path method of the Node object dances with grace."""
    s = fs_db.FSDB(self.root)
    
    for path in s.keys():
      self.assertTrue(s[path].path()==path)
    
    del s
  
  
  def test_node_real_path(self):
    """Tests that real paths are comming back correctly."""
    s = fs_db.FSDB(self.root)
    
    for node in s.values():
      rp = os.path.join(*([self.root] + list(node.path())))
      self.assertTrue(node.real_path()==rp)
    
    del s


  def test_node_contains(self):
    """Tests the contains capability of the Node object."""
    s = fs_db.FSDB(self.root)
    
    self.assertTrue('cabbage.txt' in s[()])
    self.assertTrue('turnip.txt' in s[()])
    self.assertTrue('penguins' in s[()])
    self.assertFalse('cats.txt' in s[()])
    
    self.assertTrue('fly.txt' in s['penguins'])
    self.assertFalse('breakdance.txt' in s['penguins'])
    
    del s


  def test_node_get(self):
    """Tests the getitem method of the Node object is a good provider, and therfore worthy of marriage."""
    s = fs_db.FSDB(self.root)
    
    self.assertTrue(s[()]['cabbage.txt'].path()==('cabbage.txt',))
    self.assertTrue(s[()]['penguins']['fly.txt'].path()==('penguins','fly.txt'))
    
    with self.assertRaises(KeyError):
      s[()]['cats.txt']
      
    with self.assertRaises(KeyError):
      s[()]['penguins']['astronaut.txt']
      
    with self.assertRaises(KeyError):
      s[()]['cabbage.txt']['astronaut.txt']
    
    del s
  
  
  def test_node_iter(self):
    """Tests that you can iterate the contents of a node."""
    s = fs_db.FSDB(self.root)
    
    names = []
    for name in s[()].keys():
      names.append(name)
    expected = {'cabbage.txt', 'turnip.txt', 'penguins'}
    self.assertTrue(set(names)==expected)
    
    names = []
    for name in s['penguins'].keys():
      names.append(name)
    expected = {'fly.txt'}
    self.assertTrue(set(names)==expected)
    
    del s
  
  
  def test_node_len(self):
    """Tests that length works as expected."""
    s = fs_db.FSDB(self.root)
    
    self.assertTrue(len(s[()])==3)
    self.assertTrue(len(s['penguins'])==1)
    self.assertTrue(len(s['penguins','fly.txt'])==0)
    
    del s
  
  
  def test_cache_dir(self):
    """Tests that directory contents caching works."""
    s = fs_db.FSDB(self.root)
    s.set_cache_time(1.0)
    
    open(os.path.join(self.root, 'snails.txt'), 'w').close()
    
    self.assertFalse('cats.txt' in s[()])
    self.assertTrue('snails.txt' in s[()])
    
    open(os.path.join(self.root, 'cats.txt'), 'w').close()
    os.remove(os.path.join(self.root, 'snails.txt'))
    
    self.assertFalse('cats.txt' in s[()])
    self.assertTrue('snails.txt' in s[()])
    
    time.sleep(1.5)
    
    self.assertTrue('cats.txt' in s[()])
    self.assertFalse('snails.txt' in s[()])
    
    del s



class TestFSDB_Json(unittest.TestCase):
  """Tests the JSON reading/writting plugin for FSDB."""
  def setUp(self):
    self.temp_dir = tempfile.TemporaryDirectory()
    self.root = self.temp_dir.name
    self.fsdb = fs_db.FSDB(self.root)
    self.fsdb.register(fs_db_json.JsonFileType())
    
    open(os.path.join(self.root, 'wibble.txt'), 'w').close()
        
    f = open(os.path.join(self.root, 'swan.json'), 'w')
    f.write('{"name":"Percy", "age":5}')
    f.close()
  
  
  def tearDown(self):
    del self.fsdb
    self.temp_dir.cleanup()
  
  
  def cycle(self):
    """Helper - creates a new fsdb to effectivly reset all cached data."""
    del self.fsdb
    self.fsdb = fs_db.FSDB(self.root)
    self.fsdb.register(fs_db_json.JsonFileType())
  
  
  def test_sanity(self):
    """Just to make sure nothing basic is broken."""
    self.assertTrue('swan.json' in self.fsdb.get_root())
  
  
  def test_type(self):
    """Check the filetype method is working."""
    self.assertTrue(self.fsdb['wibble.txt'].filetype()==None)
    self.assertTrue(self.fsdb['swan.json'].filetype().extension()=='.json')
  
  
  def test_read(self):
    """Read in files, check the right stuff happens."""
    data = self.fsdb['swan.json'].read()
    self.assertTrue(data['name']=='Percy')
    
    time.sleep(0.1)
    
    f = open(os.path.join(self.root, 'swan.json'), 'w')
    f.write('{"name":"Louise", "age":5}')
    f.close()
    
    data = self.fsdb['swan.json'].read()
    self.assertTrue(data['name']=='Louise')
    
    with self.assertRaises(TypeError):
      self.fsdb['wibble.txt'].read()
  
  
  def test_write(self):
    """Write files - check it behaves itself."""
    
    self.fsdb['swan.json'].write({'name' : 'Paul'})
    
    data = self.fsdb['swan.json'].read()
    self.assertTrue(data['name']=='Paul')
    
    self.cycle()
    
    data = self.fsdb['swan.json'].read()
    self.assertTrue(data['name']=='Paul')
  
  
  def test_new(self):
    """Tests the ability to create new files."""
    
    p = self.fsdb.get_root().new('penguins')
    self.assertTrue(p.path()==('penguins',))
    
    p.new('eat.json', ['babies', 'presidents'])
    d = self.fsdb['penguins','eat.json'].read()
    self.assertTrue('babies' in d)
    self.assertFalse('fishies' in d)
    
    self.cycle()
    
    d = self.fsdb['penguins','eat.json'].read()
    self.assertTrue('babies' in d)
    self.assertFalse('fishies' in d)
  
  
  def test_clone(self):
    """Tests the clone capability."""
    alt_temp_dir = tempfile.TemporaryDirectory()
    path = os.path.join(alt_temp_dir.name, 'bear.json')
    
    f = open(path, 'w')
    f.write('{"name":"Cleese"}')
    f.close()
    
    self.fsdb[()].clone('cabbage.json', path)
    self.fsdb[()].clone('sprout.json', self.fsdb['swan.json'])
     
    alt_temp_dir.cleanup()
    
    self.assertTrue(self.fsdb['cabbage.json'].read()['name']=='Cleese')
    self.assertTrue(self.fsdb['sprout.json'].read()['name']=='Percy')
    
    self.cycle()
 
    self.assertTrue(self.fsdb['cabbage.json'].read()['name']=='Cleese')
    self.assertTrue(self.fsdb['sprout.json'].read()['name']=='Percy')
  
  
  def test_create(self):
    """Tests that the create method works."""
    self.fsdb.get_root().create('fish')
    self.assertTrue('fish' in self.fsdb)
    
    self.fsdb.get_root().create(('fish', 'dancing', 'drunk'))
    self.assertTrue(['fish', 'dancing', 'drunk'] in self.fsdb)
    
    with self.assertRaises(TypeError):
      self.fsdb.get_root().create('swan.json')
    
    with self.assertRaises(TypeError):
      self.fsdb.get_root().create(('wibble.txt', 'cabbage'))

    self.fsdb.get_root().create('fish')
