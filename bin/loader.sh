#!/bin/bash
#
# Title: loader.sh
# Description: load heeler files
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
hostname=$(hostname)
logger -p local3.info "heeler loader $hostname"
#
echo "start loader"
#
docker rm heeler;docker run -v /var/peccary/heeler:/mnt/peccary/heeler --name heeler heeler:latest
#
echo "end loader"
#
