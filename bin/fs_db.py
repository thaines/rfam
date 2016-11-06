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
import shutil
import time
import datetime

import json
import collections

from .lock_file import lock_dir_prefix, LockFile



class FileType:
  """Interface for a filetype, which will enable the read and write methods of the Node method for files with this type when registered with the State object."""
  def extension(self):
    """Returns the extension that files should have to match this file type, checked with endswith - should include the dot."""
    raise NotImplementedError
  
  def read(self, f):
    """Given a readable file object this reads the file in and returns an object representing it, that will be cached and provided to the user."""
    raise NotImplementedError
  
  def write(self, f, data):
    """Given a writable file object and the data associated (in the same form as read returns) this should write it to the file."""
    raise NotImplementedError
  


class Node(collections.Mapping):
  """Represents a node in the filesystem, be it file or directory. Provides a slightly weird if useful interface to it!"""
  UNINITIALISED = 0
  DELETED = 1
  DIRECTORY = 2
  FILE = 3
  
  __slots__ = ['owner', 'parent', 'name', 'cache_real_path', 'state', 'ftype', 'update', 'contents', 'ext']
  
  def __init__(self, owner, parent, name):
    self.owner = owner
    self.parent = parent
    self.name = name
    
    self.cache_real_path = None # Its slow to calculate, so cache it.
    
    self.state = Node.UNINITIALISED
    self.ftype = None # The file type object that matches this filename; None if no associated type.
    self.update = None # When it was last updated.
    self.contents = None # Depends on what it is - for directories its a dict[child] -> Node.
    self.ext = None
    
    for ext, ft in owner.types.items():
      if self.name.endswith(ext):
        self.ftype = ft
        break
  
  
  def isa(self):
    """Returns what it is - either DELETED, DIRECTORY or FILE. Note that this will make sure everything is upto date as required, so this doubles as a cache-checking method."""
    # If it hasn't been initialised make it do so...
    if self.state==Node.UNINITIALISED:
      path = self.real_path()
      
      if not os.path.exists(path):
        self.state = Node.DELETED
      elif os.path.isdir(path):
        self.state = Node.DIRECTORY
      else:
        self.state = Node.FILE
      
      if self.state==Node.DIRECTORY:
        # Make sure it contains the correct directory contents...
        self.update = time.time()
        
        self.contents = dict()
        try:
          fns = os.listdir(path)
        except OSError:
          fns = []
        
        for fn in fns:
          if not fn.startswith(lock_dir_prefix):
            self.contents[fn] = Node(self.owner, self, fn)

      return self.state # No need to check stuff - we just updated it!
    
    # If its a directory its contents cache may be out of date...
    if self.state==Node.DIRECTORY:
      t = time.time()
      if (self.update + self.owner.cache_time) < t:
        self.update = t
        self.ext = None # Reset contents cache.
        path = self.real_path()
        fnl = set(os.listdir(path))
        
        # Delete stuff that no longer exists...
        for die in (self.contents.keys() - fnl):
          del self.contents[die]
        
        # Add new stuff...
        for birth in (fnl - self.contents.keys()):
          if not birth.startswith(lock_dir_prefix):
            self.contents[birth] = Node(self.owner, self, birth)
     
    return self.state


  def path(self):
    """Returns the tuple that is the full path of this node."""    
    def make_path(node):
      while node.parent!=None:
        yield node.name
        node = node.parent
    
    return tuple(make_path(self))[::-1]
  
  
  def real_path(self):
    """Returns the real filename of the node - a straight string that can be passed to functions like open etc."""
    if self.cache_real_path==None:
      def make_path(node):
        while True:
          if node.parent==None:
            yield node.owner.root
            return
          yield node.name
          node = node.parent
      self.cache_real_path = os.path.join(*list(make_path(self))[::-1])
      
    return self.cache_real_path
  
  
  def filetype(self):
    """Returns the FileType object associated with this file, or None if there is no such type."""
    return self.ftype


  def read(self):
    """Reads the file and returns an object representing it. Note that the object may be cached for future calls to read, and therefore must not be edited (Unless it is to be immediatly sent to the write method)."""
    if self.ftype==None:
      raise TypeError('File type does not have a registered file handler')
    
    rpath = self.real_path()
    fmtime = os.path.getmtime(rpath) # Less than ideal, but ns resolution not avalible on version of python I am using:-/
    
    if self.update==None or self.update<fmtime:
      self.update = fmtime
      if self.owner.single_proc:
        f = open(rpath, 'r')
        self.contents = self.ftype.read(f)
        f.close()
      else:
        with LockFile(rpath, 'r') as f:
          self.contents = self.ftype.read(f)
    
    return self.contents
  
  
  def write(self, data):
    """Writes the given data into the file, the details of which are FileType dependent. The data will also be stored in the files cache ready to be reused, so after a call to write data must not be edited, unless it is to be written again, which would not be very efficient. Note that this locks the file using a directory to make sure its totally safe."""
    if self.ftype==None:
      raise TypeError('File type does not have a registered file handler')
    
    rpath = self.real_path()
    
    if self.owner.single_proc:
      f = open(rpath, 'w')
      self.ftype.write(f, data)
      f.close()
    else:
      with LockFile(rpath, 'w') as f:
        self.ftype.write(f, data)
    
    self.update = os.path.getmtime(rpath) # Less than ideal, but ns resolution not avalible on version of python I am using:-/
    self.contents = data
  
  
  def modified(self):
    """Returns the last modification time of the node - direct from operating system. As a datetime object."""
    rpath = self.real_path()
    mtime = os.path.getmtime(rpath)
    return datetime.datetime.fromtimestamp(mtime)
  
  
  def size(self):
    """Returns the size of the node in bytes; will be zero for directories."""
    rpath = self.real_path()
    try:
      return os.path.getsize(rpath)
    except OsError:
      return 0
  
  
  def new(self, name, data = None):
    """Creates a new Node as a child of this one, which must be a Directory. Returns the new node. You provide a name, from which it infers a FileType, and some data, which is written using the FileType-s write method. If the node already exists it is overwritten, and its equivalent to a write on that node. Its obviously dependent on a FileType for the given name having been registered. If data is None, the default, it creates a new directory."""
    if self.isa()!=Node.DIRECTORY:
      print(self.real_path())
      raise TypeError('Can only create entities within directories')
    
    if data==None:
      # Special case directory creation...
      if name in self.contents: return self.contents[name]
      
      ret = Node(self.owner, self, name)
      self.contents[name] = ret
      
      os.makedirs(ret.real_path())
      
      return ret
    
    if name in self.contents:
      ret = self.contents[name]
      if ret.isa()!=Node.FILE:
        raise TypeError('Can not write data into a directory')
    else:
      ret = Node(self.owner, self, name)
      self.contents[name] = ret
    
    ret.write(data)
    
    return ret
      
    
  def clone(self, name, source):
    """Creates a new file storing it within this Node (Must be a directory) with the given name. If a node with the given name already exists it is overriden. It returns the new (or old) Node. source is another Node in a FSDB structure. Note that it does not do directories."""
    if self.isa()!=Node.DIRECTORY:
      raise TypeError('Can only create files within directories')
    
    if name in self.contents:
      ret = self.contents[name]
      if ret.isa()!=Node.FILE:
        raise TypeError('Cannot replace a directory with a file')
      ret.update = None
      ret.contents = None
    else:
      ret = Node(self.owner, self, name)
      self.contents[name] = ret
    
    fn = source.real_path() if isinstance(source, Node) else source
    
    shutil.copy2(fn, ret.real_path())
    
    return ret
  
  
  def create(self, key):
    """Given a key to a child node this ensures that it exists, as a sequence of directories. Also works for a single item if you just want a subdirectory of this node. Note that if the node already exists its a no-op. If any nodes on the path already exist and are not directories a TypeError will be thrown however. Returns the final node."""
    if isinstance(key, str):
      key = (key,)

    if self.isa()!=Node.DIRECTORY:
      if self.isa()==Node.DELETED:
        os.makedirs(ret.real_path())
      else:
        raise TypeError

    if len(key)==0: return self
    
    if key[0] not in self.contents:
      os.mkdir(os.path.join(self.real_path(), key[0]))
      self.contents[key[0]] = Node(self.owner, self, key[0])
    
    return self.contents[key[0]].create(key[1:])
  
  
  def remove(self):
    """Removes this node - only works for files."""
    if self.isa()!=Node.FILE:
      raise TypeError('System cannot remove directories')
    
    os.unlink(self.real_path())
    self.state = Node.DELETED
    
    del self.parent.contents[self.name]

  
  def iterate(self, path = None):
    """Iterates all items in this directory and subdirectories - should yield the same number of items that count outputs, ignoring the possibility that the state can change between calls. Will also yield itself; yields full paths, with the optional input the same as a call to path on this Node, but as a list - used internally to speed things up."""
    t = self.isa()
    
    if t==Node.DELETED: return
    
    if path==None:
      path = list(self.path())
    yield tuple(path)
    
    if t==Node.FILE: return
      
    # t==Node.DIRECTORY
    for name, child in self.contents.items():
      for ret in child.iterate(path + [name]):
        yield ret
  
  
  def iterate_ext(self, ext, path = None, exclude = None):
    """Same as iterate, except it only returns files with the given extension - a little bit more efficient than filtering yourself. exclude is an optional regular expression - directories that match are not iterated into."""
    t = self.isa()
    
    if t==Node.DELETED: return
    
    if path==None:
      path = list(self.path())
    
    if t==Node.FILE:
      if self.ext==None:
        self.ext = self.name.endswith(ext)
      if self.ext:
        yield tuple(path)
      return
      
    # t==Node.DIRECTORY
    for name, child in self.contents.items():
      if (exclude==None or not exclude.match(name)) and child.contains_ext(ext):
        for ret in child.iterate_ext(ext, path + [name]):
          yield ret


  def count(self):
    """Returns the number of items in this Node plus all of its children nodes, counting itself - unlike len it does the entire hierarchy."""
    t = self.isa()
    
    if t==Node.DELETED:
      return 0
      
    if t==Node.FILE:
      return 1
    
    # t==Node.DIRECTORY
    ret = 1
    for child in self.contents.values():
      ret += child.count()
    return ret
  
  
  def contains_ext(self, ext):
    """Returns true if this node is a file with the given extension, or is a directory that contains (recursive) files with the given extension - allows you to efficiently cull when iterating files with a given extension, noting that it caches its answer."""
    t = self.isa()
    
    if t==Node.DELETED:
      return False
    
    if t==Node.FILE:
      if self.ext==None:
        self.ext = self.name.endswith(ext)
      return self.ext
    
    # t==Node.Directory
    if self.ext==None:
      self.ext = dict()
    
    if ext not in self.ext:
      val = False
      for child in self.contents.values():
        val = child.contains_ext(ext)
        if val: break
      self.ext[ext] = val
    
    return self.ext[ext]


  def __contains__(self, key):
    if self.isa()!=Node.DIRECTORY:
      return False
    
    return key in self.contents
    
    
  def __getitem__(self, key):
    if self.isa()!=Node.DIRECTORY:
      raise KeyError('Not a directory')
    return self.contents[key]
  
  
  def __iter__(self):
    if self.isa()!=Node.DIRECTORY:
      return
    
    for key in self.contents.keys():
      yield key
  
  
  def __len__(self):
    if self.isa()!=Node.DIRECTORY:
      return 0
    
    return len(self.contents)



class FSDB(collections.Mapping):
  """Caches the state of the directory hierarchy its passed on initialisation, under the assumption that other proceses may change the structure. It does cache however, and only checks periodically, so out of date answers are possible for directory contents. For file contents the query is guaranteed to be millisecond recent as it checks time stamps. Caches the contents of files for which a handler is registered. Acts as a mapping type that accesses everything in the hierarchy via tuples of strings (!), with an empty tuple obtaining the root Node. Note that internally it uses directories prefixed with '.lock_' for file locks, so don't try and use nodes with that prefix as they will be hidden."""
  def __init__(self, root, single_proc = False):
    """Root is the root directory of the hierarchy to cache. single_proc can be set to False to stop it using lock files - this makes reading a hell of a lot faster, but is unsafe if their are multiple processes!"""
    self.root = os.path.normpath(root)
    self.single_proc = single_proc
    self.cache_time = 30.0
    
    self.types = dict() # Dictionary from extension to FileType object.
    
    self.node = Node(self, None, None)
  
  
  def get_cache_time(self):
    """Returns how long it caches the contents of a directory for before refreshing it, in seconds as a float."""
    return self.cache_time
    
  def set_cache_time(self, time):
    """Allows you to set the cache time, in floating point seconds."""
    self.cache_time = float(time)
  
  
  def register(self, ft):
    """Allows you to register a filetype with the State object, enabling the read and write methods for that filetype."""
    self.types[ft.extension()] = ft


  def get_root(self):
    """Returns the root Node object, that is the start of the hierarchy."""
    return self.node
    
  
  def __contains__(self, key):
    """Returns True if the given exists in the directory structure, False if it does not."""
    if isinstance(key, str):
      key = (key,)
    
    targ = self.node
    for part in key:
      targ.isa() # Makes sure its up to date.
      if part not in targ: return False
      targ = targ[part]
    
    return True


  def __getitem__(self, key):
    """Allows you to access everything in the directory structure - index with a single item to select from the root directory, or with a tuple to select some random item. Returns a Node object. Note that, compliments of numpy, you don't need tuple brackets when indexing, i.e. ['subdir','subsubdir'] will work."""
    if isinstance(key, str):
      key = (key,)
    
    targ = self.node
    for part in key:
      targ.isa() # Makes sure its upto date.
      targ = targ[part]
    
    return targ


  def __iter__(self):
    """Iterates everything - every entity in the hierarchy."""
    for node in self.node.iterate():
      yield node


  def __len__(self):
    """Returns how many items will be iterated by iter... ignoring the temporal aspect where it could actually change half way through iterating! In other words, don't make that assumption."""
    return self.node.count()
