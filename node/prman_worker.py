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

import time
import os
import re
import json

import threading
import subprocess
from collections import namedtuple
if not hasattr(subprocess, 'DEVNULL'):
  subprocess.DEVNULL = open(os.devnull, 'w')


class prman_Worker:
  """Simple entity for managing a seperate process that is running a render in Blender - simple wrapper that handles all the tedious Blender-specific stuff."""
  def __init__(self, node, threads = 1, printDebug = False):
    """Provided with the Node object and the number of threads to pass through to Blender each time it is run."""
    self.node = node
    self.threads = threads
    
    # Process into which its running something, None if nothing has been run...
    self.proc = None
    
    # Other state...
    self.uuid = None
    self.fn = None
    self.frame = None
    self.frameCommands = None
    self.frameCommandsTODO = 0
    self.start = time.time()
    self.last_line = ''
    self.printDebug = printDebug

    #lists to hold outputs
    self.outLogs = []
    self.errLogs = []
  
  
  def busy(self):
    #always return true if there is more work to do for the current frame command stack
    if self.frameCommandsTODO > 0:
      if self.printDebug:
        print('WORKER: Busy, frameCommands: ', self.frameCommandsTODO)
      return True
    
    #else check if the last task has finished processing and return appropriately...
    """Returns True if the worker has work, False if it does not."""
    busy = not (self.proc==None or self.proc.poll()!=None)
    if self.printDebug:
      print('WORKER: BUSY: ', busy)
    return busy
  
  def p(self):
    """Returns the process, or None if its not running, so it can wait for something to happen."""
    #always return true if there is more work to do for the current frame command stack
    if self.frameCommandsTODO > 0:
      dummyJob = namedtuple('dummyJob', 'poll')
      instance = dummyJob(poll = (lambda : None))
      return instance #dummy object
    
    #otherwise, check if a process is running
    if self.proc!=None and self.proc.poll()==None:
      return self.proc
    else:
      return None
  
  
  def state(self):
    """Either returns the state of the node or None, if there is no state to return. Note that when a task completes it may not be busy but it still has to return that it completed the job."""
    if self.proc==None:
      return None
    
    poll = self.proc.poll()
    #we are still working as long as there are todos that need to be done
    if self.frameCommandsTODO > 0 or poll==None:
      # Still running...
      done = 0
      total = 1
      if self.printDebug:
        print('WORKER: Still running!')
      return {'id' : 'report', 'uuid' : self.uuid, 'frame' : self.frame, 'done' : done, 'total' : total}
    elif poll==0:
      # Finished running and has not told server this fact...
      self.proc = None # Remove the process - the server now knows its done.
      now = time.time() # Some potential inaccuracy here, but no easy solution
      if self.printDebug:
       print('WORKER: Done!')
      return {'id' : 'done', 'uuid' : self.uuid, 'frame' : self.frame, 'time' : now - self.start}
    else:
      # Something has gone wrong - give up...
      if self.printDebug:
        print('WORKER: An unknown error has occured!')
      return None


  def run(self, commandment):
    """Only call if busy is False - sets a job running and state has been called. commandment must be a dictionary returned by the server with an id of task."""
    if (not isinstance(commandment['frame'], int)):
      return # Drop video commandments - server isn't going to like this, but meh.
    
    self.uuid = commandment['uuid']
    self.frame = commandment['frame']
    
    self.fn = self.node.to_local(commandment['file'])
    self.cwd = os.path.dirname(os.path.abspath(self.fn))

    self.frameCommands = commandment['prmanCommands']['commands']['frames'][str(self.frame)]
    self.frameCommandsTODO = len(self.frameCommands)

    #create a unique name for the log file
    self.currentLogFileName = os.path.abspath(self.cwd + '/log_' + str(time.time()).replace('.', '') + '.txt')
    
    if self.printDebug:
      print('NOTE: Worker received new commands: ', self.frameCommands)

    if isinstance(self.frame, int):
      start = self.frame
      end = self.frame
      self.video = False
    else:
      if self.printDebug:
        print('ERROR: rfam video functionality is not yet support by the prman worker type!')
      #video is not supported by this worker type
      self.kill_all()

    if self.printDebug:
      attrs = vars(self)
      print(', '.join("%s: %s" % item for item in attrs.items()))
    self.launchNextCommand()

  def kill(self, commandment):
    """Given a commandment with an id of kill it does it, but only if the details match."""
    if self.proc!=None and commandment['uuid']==self.uuid and commandment['frame']==self.frame:
      self.frameCommandsTODO = 0
      self.proc.kill()
      self.proc.wait()
      self.proc = None
  
  def kill_all(self):
    """For when you just want it all dead."""
    if self.proc!=None:
      self.frameCommandsTODO = 0
      self.proc.kill()
      self.proc.wait()
      self.proc = None
  
  #a couple of helper functions to aid in parsing commands
  def replace_cwd_arg(self, command, replacement):
    start = command.find(' -cwd')
    #if there is no such argument, just return
    if start == - 1:
      return command

    #else find the end of the command string
    end = -1
    parsingParenthesis = False
    for i in range(start + 6, len(command)):
      if command[i] == "\"":
        if parsingParenthesis:
          end = i
          break
        else:
          parsingParenthesis = True
      if not parsingParenthesis and command[i] == ' ':
        end = i
        break
    #make sure to return as normal if this went wrong
    if end == -1:
      return command
    
    #else, replace the substring
    if parsingParenthesis:
      oldCommand = command[start+1:end+1]
    else:
      oldCommand = command[start+1:end+1]

    return command.replace(oldCommand, replacement)

  def replace_threads_arg(self, command, replacement):
    start = command.find('-t')
    #is this argument doesn't exit, we append it
    if start == -1:
      if replacement == -1:
        return command + ' -t:' + str(replacement)
      else:
        return command + ' -t:' + str(replacement)
    
    #otherwise, replace the existing argument
    if command[start:start+5] == '-t:-1':
      return command.replace('-t:-1', '-t:' + str(replacement))
    else:
      end = -1
      for i in range(start + 3, len(command)):
        if command[i] == ' ':
          end = i
          break
      if end == -1:
        return command
      else:
        return command.replace(command[start:end+1], '-t:' + str(replacement))

  def replace_denoise_paths(self, command):
    quoted_paths = re.findall(r'\"(.+?)\"', command)
    for p in quoted_paths:
      command = command.replace(p, os.path.join(self.cwd, p))
    if self.printDebug:
      print('WORKER: New Denoise Command: ', command)
    return command

  def launchNextCommand(self):
    #get the current command
    nextCommand = self.frameCommands[len(self.frameCommands) - self.frameCommandsTODO]['command']
    
    if nextCommand.startswith('denoise'):
      #make the denoise paths absolute relative to current node
      nextCommand = self.replace_denoise_paths(nextCommand)
      #override thread count if necessary 
      if self.node.config["prman_override_thread_count"]:
        nextCommand = self.replace_threads_arg(nextCommand, self.threads)

    elif nextCommand.startswith('prman'): 
      #rebuild the RemoteCmd for the target configuration
      nextCommand = self.replace_cwd_arg(nextCommand, '-cwd \"' + self.cwd + '\"')
      if self.node.config["prman_override_thread_count"]:
        nextCommand = self.replace_threads_arg(nextCommand, self.threads)
    else:
      if self.printDebug:
        print('WARNING: command structure unknown for [ ' + nextCommand + " ].")

    #finally, do the call (wrapped in callback to handle multiple commands)
    self.popenAndCall(nextCommand)
  
  def onExit(self):
    if self.printDebug:
      print('WORKER: OnExit', self.frameCommandsTODO)
    
    #decrease the command counter
    self.frameCommandsTODO -= 1
    self.procInitialised = False
    #if its zero, just do nothing
    #otherwise, launch the next command
    if self.frameCommandsTODO > 0:
      self.launchNextCommand()
    else:
      #make sure to write output to log file
      if self.printDebug:
        print('OUT: ', self.outLogs)
        print('ERR: ', self.errLogs)
      if self.node.config['prman_write_log_files']:
        try:
          with open(self.currentLogFileName, 'w') as outfile:
            json.dump({'stdout' : self.outLogs, 'stderr' : self.errLogs}, outfile)
        except Exception as e:
          print('ERROR: File ' + self.currentLogFileName + ' could not be written.')
      
      self.frameCommandsTODO = 0
      self.proc = None
      self.outLogs = []
      self.errLogs = []
  
  def runInThread(self, popenArgs):
    #create an environment with prman's bin directory in the path
    my_env = os.environ.copy()

    if os.name == 'nt':
      my_env["PATH"] = my_env["PATH"] + ';' + self.node.config["prman_path"]
    else:
      my_env["PATH"] = my_env["PATH"] + ':' + self.node.config["prman_path"]
    #always set RMANTREE
    my_env['RMANTREE'] = self.node.config['prman_rmantree']

    if self.printDebug:
      print('NOTE: Thread command: ', popenArgs)
      print('ENV: ', env)

    #run the command in that environment
    self.proc = subprocess.Popen(popenArgs,
      universal_newlines = True,
      env = my_env,
      shell = True,
      stdout = subprocess.PIPE, stderr=subprocess.PIPE,
      bufsize = -1)
    
    #use to prevent race condition occuring because of thread launch time
    self.procInitialised = True

    self.start = time.time()
    #this will include a call to subprocess.wait()
    #append out and err to already existing logs
    out, err = self.proc.communicate()
    self.outLogs.append(out)
    self.errLogs.append(err)

    if self.printDebug:
      print('NOTE: Finished Thread!')
    self.onExit()
  
  #see https://stackoverflow.com/questions/2581817/python-subprocess-callback-when-cmd-exits
  def popenAndCall(self, popenArgs):
    """
    Runs the given args in a subprocess.Popen, and then calls the function
    onExit when the subprocess completes.
    onExit is a callable object, and popenArgs is a list/tuple of args that 
    would give to subprocess.Popen.
    """
    self.procInitialised = False #set this to false
    thread = threading.Thread(target=self.runInThread, args=(popenArgs,))
    thread.start()
    #wait until the thread is actually running
    while True:
      if self.procInitialised == True:
        break