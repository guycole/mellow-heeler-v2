#!/bin/bash
#
# Title: collector.sh
# Description: drive the iwlist parse pass
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
# */10 * * * * /home/wombat/Documents/github/mellow-heeler-v2/bin/collector.sh > /dev/null 2>&1
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
WORK_DIR="/home/wombat/Documents/github/mellow-heeler-v2/src/wombat_collector"
#
echo "start collector"
cd $WORK_DIR
source venv/bin/activate
python3 ./collector.py
echo "end collector"
#
