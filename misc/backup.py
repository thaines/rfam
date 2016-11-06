#! /usr/bin/env python

import os.path
from subprocess import call



# Generate the sequence of backup directories...
base = '/backups/3dami/'
step = 10 # In minutes - gap between each backup
length = 24 * 60 # How long to keep backups for

backup_seq = []
for minutes in xrange(0, length+1, step):
  code = 't_%02i_%02i' % (minutes//60, minutes%60)
  backup_seq.append(os.path.join(base, code))



# Terminate the very last backup...
call(['rm', '-rf', backup_seq[-1]])



# Do the moves...
for source, origin in zip(backup_seq[1:-1], backup_seq[2:])[::-1]:
  call(['mv', source, origin])



# Make a full copy for the most recent state change...
call(['cp', '-al', backup_seq[0], backup_seq[1]])



# Use rsync to make the backup...
source = '/3Dami/projects/'
call(['rsync', '-av', '--delete', source, backup_seq[0]])

