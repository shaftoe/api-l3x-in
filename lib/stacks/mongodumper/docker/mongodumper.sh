#!/bin/bash
set -u
set -e
set -o pipefail

trap "{ printf 'ERROR: catched non-zero exit code\n'; exit 1; }" ERR

TODAY="$(date +%Y-%m-%d)"
DST_FILE="s3://${S3_BUCKET}/mongodump-${TODAY}.gz"

mongodump \
    --archive \
    --gzip \
    --ssl \
    --uri="${MONGODB_URI}" \
    | aws s3 cp - ${DST_FILE}

printf "INFO: All done, exiting with code 0\n"
exit 0
