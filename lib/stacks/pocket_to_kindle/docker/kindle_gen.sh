#!/bin/bash
trap "{ printf 'ERROR: catched non-zero exit code\n'; exit 1; }" ERR

SRC_FILE="s3://${EPUB_SRC_BUCKET}/${EPUB_SRC_KEY}"
MOBI_DEST_KEY="$(echo ${EPUB_SRC_KEY} | sed 's/\.epub$/.mobi/')"
DST_FILE="s3://${MOBI_DEST_BUCKET}/${MOBI_DEST_KEY}"

printf "INFO: Fetch S3 key ${SRC_FILE}\n"
aws s3 cp "${SRC_FILE}" file.epub

printf "INFO: Run kindlegen binary\n"
kindlegen file.epub || true  # NOTE: creates file.mobi

printf "INFO: Put kindlegen generated file.mobi to ${DST_FILE}\n"
aws s3 cp file.mobi "${DST_FILE}"

printf "INFO: All done, exiting with code 0\n"
exit 0
