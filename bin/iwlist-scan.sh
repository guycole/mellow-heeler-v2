#!/bin/bash
#
# Title: iwlist-scan.sh
# Description: scan for wireless access points
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
# must run from root crontab
# * * * * * /home/wombat/Documents/github/mellow-heeler-v2/bin/iwlist-scan.sh > /dev/null 2>&1
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
FILENAME="/tmp/iwlist.scan"
#
echo "start scan"
unlink $FILENAME
/sbin/iwlist scan > $FILENAME
chmod 666 $FILENAME
echo "end scan"
#
