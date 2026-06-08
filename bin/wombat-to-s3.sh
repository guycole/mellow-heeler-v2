#!/bin/bash
#
# Title: wombat-to-s3.sh
# Description: move heeler files local file system to s3
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
ARCHIVE_DIR="archive"
EXPORT_DIR="export"
WORK_DIR="/var/wombat/heeler"
#
DEST_BUCKET=s3://mellow-heeler-uw2-k2718.braingang.net/fresh/
#
echo "start s3 move"
cd /var/mellow/heeler/fresh; gzip *
aws s3 mv . $DEST_BUCKET --recursive --profile=wombat04
echo "end s3 move"
