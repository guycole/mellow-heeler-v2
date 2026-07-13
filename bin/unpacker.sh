#!/bin/bash
#
# Title: unpacker.sh
# Description: unpack fresh tar files and move to archive
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
hostname=$(hostname)
logger -p local3.info "unpacker heeler $hostname"
#
ARCHIVE_DIR="/var/peccary/heeler/archive"
WORK_DIR="/var/peccary/heeler"
#
echo "start unpacker"
#
cd ${WORK_DIR}
for file in fresh/*; do
  echo "$file"
  tar -xzf ${file}
  mv ${file} ${ARCHIVE_DIR}
done
#
echo "end unpacker"
#
