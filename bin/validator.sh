#!/bin/bash
#
# Title: validator.sh
# Description: verify collection files and update stats for wombat
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
CONTAINER1="wombat-heeler"
CONTAINER2="koala-heeler"
IMAGE="ghcr.io/guycole/wombat-heeler:latest"
#
echo "start validate"
#
docker rm ${CONTAINER1};docker run --entrypoint python -v /var/wombat:/mnt/wombat --name ${CONTAINER1} ${IMAGE} heeler_app.py
#
docker rm ${CONTAINER2};docker run --entrypoint python -e stuntbox=koala -v /var/wombat:/mnt/wombat --name ${CONTAINER2} ${IMAGE} heeler_app.py
$HOME/github/mellow-heeler-v2/bin/koala-import.sh
#
echo "end validate"
#
