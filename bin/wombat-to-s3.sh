#!/bin/bash
#
# Title: wombat-to-s3.sh
# Description: copy heeler files local file system to s3
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
# host name is also AWS profile name
HOST_NAME=$(hostname)
#
EXPORT_DIR="export"
WORK_DIR="/var/wombat/heeler"
#
DEST_BUCKET=s3://mellow-heeler-uw2-k2718.braingang.net/fresh/
#
echo "start s3 copy"
cd "${WORK_DIR}/${EXPORT_DIR}" || exit 1

if aws s3 mv . "$DEST_BUCKET" --recursive --profile="$HOST_NAME"; then
	: # files removed by s3 mv
else
	echo "s3 mv failed" >&2
	exit 1
fi

echo "end s3 copy"
