#!/bin/bash
#
# Title: validator.sh
# Description: verify collection files and update stats for wombat
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
echo "start validate"
#
docker rm heeler-validate;docker run -v /var/wombat:/mnt/wombat --name heeler-validate heeler:latest
#
docker rm heeler-koala;docker run -e stuntbox=koala -v /var/wombat:/mnt/wombat --name heeler-koala heeler:latest
$HOME/github/mellow-heeler-v2/bin/koala-import.sh
#
echo "end validate"
#
