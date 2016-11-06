#!/bin/bash

### BEGIN INIT INFO
# Provides: rfam
# Required-Start: $remote_fs $syslog $network
# Required-Stop: $remote_fs $syslog $network
# Default-Start: 3 4 5
# Default-Stop: 0 1 2 6
# Short-Description: Integrated render farm and asset manager for 3D animated film creation
### END INIT INFO

case "$1" in
	start)
		nohup su - tom -c /home/tom/rfam/go.sh > /home/tom/rfam/log.txt &
		;;
	stop)
		killall python3
		;;
esac
exit 0	

