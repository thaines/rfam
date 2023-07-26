#! /usr/bin/env python3

import os
import datetime
from subprocess import call



# Generate the sequence of backup directories...
base = '/backups/'
step = 10 # In minutes - gap between each backup
length = 24 * 60 # How long to keep backups for

backup_seq = []
for minutes in range(0, length+1, step):
  code = 't_%02i_%02i' % (minutes//60, minutes%60)
  backup_seq.append(os.path.join(base, code))



# Terminate the very last backup...
call(['rm', '-rf', backup_seq[-1]])



# Do the moves...
for source, origin in list(zip(backup_seq[1:-1], backup_seq[2:]))[::-1]:
  call(['mv', source, origin])



# Make a full copy for the most recent state change...
call(['cp', '-al', backup_seq[0], backup_seq[1]])



# Ensure backup folder exists...
os.makedirs(backup_seq[0], exist_ok=True)



# Use rsync to make the backup...
start = datetime.datetime.now()
source = 'server:/mnt/3Dami/'
call(['rsync', '-av', '--delete', source, backup_seq[0]])
end = datetime.datetime.now()



# Write start/end time...
with open(os.path.join(backup_seq[0], 'backup_time.txt'), 'w') as fout:
  print(f'start = {start.isoformat()}', file=fout)
  print(f'end = {end.isoformat()}', file=fout)

