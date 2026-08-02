#!/bin/bash
#
# Title: validator.sh
# Description: verify collection files and update stats for wombat
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
CONTAINER="heeler-validate"
IMAGE="ghcr.io/guycole/wombat:latest"
#
WOMBAT_UID=$(id -u wombat)
WOMBAT_GID=$(id -g wombat)
#
echo "start validate"
#
docker rm ${CONTAINER};docker run -e WOMBAT_UID=${WOMBAT_UID} -e WOMBAT_GID=${WOMBAT_GID} -v /var/wombat:/mnt/wombat --name ${CONTAINER} ${IMAGE}
#
#docker rm heeler-koala;docker run -e stuntbox=koala -e WOMBAT_UID=${WOMBAT_UID} -e WOMBAT_GID=${WOMBAT_GID} -v /var/wombat:/mnt/wombat --name heeler-koala heeler:latest
#$HOME/github/mellow-heeler-v2/bin/koala-import.sh
#
echo "end validate"
#
