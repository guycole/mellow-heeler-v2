#!/bin/bash
#
# Title: s3-to-peccary.sh
# Description: copy heeler files from s3 to peccary
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin:/opt/homebrew/bin; export PATH
#
# host name is also AWS profile name
#HOST_NAME=$(hostname)
HOST_NAME="peccary"
#
FRESH_DIR="/var/peccary/heeler/fresh"
#
SOURCE_BUCKET=s3://mellow-heeler-uw2-k2718.braingang.net/fresh/
DEST_BUCKET=s3://mellow-heeler-uw2-k2718.braingang.net/archive/
#
echo "start s3 copy"

mkdir -p "$FRESH_DIR"

aws s3 ls "$SOURCE_BUCKET" --profile "$HOST_NAME" | while read -r col1 col2 col3 object_name; do
	# Skip empty lines and pseudo-directory entries.
	if [ -z "$object_name" ] || [ "$col3" = "PRE" ]; then
		continue
	fi

	source_path="${SOURCE_BUCKET%/}/$object_name"
	local_path="$FRESH_DIR/$object_name"
	dest_path="${DEST_BUCKET%/}/$object_name"

	if aws s3 cp "$source_path" "$local_path" --profile "$HOST_NAME"; then
		aws s3 mv "$source_path" "$dest_path" --profile "$HOST_NAME"
	else
		echo "copy failed for $source_path"
	fi
done

echo "end s3 copy"