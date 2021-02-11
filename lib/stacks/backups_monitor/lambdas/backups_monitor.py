from datetime import timedelta, date
from os import environ as env
from re import match
from typing import (
    Dict,
    List,
    Tuple,
)

import utils
import utils.aws as aws
import utils.handlers as handlers

TODAY = date.today()


def _get_expected_values(bucket_name: str, retention_days: int,
                         start_day_isoformat: str = None) -> Tuple[int, date]:
    """Validate input, return exected backup list size and first backup date."""
    try:
        assert isinstance(bucket_name, str)
    except AssertionError as error:
        raise utils.HandledError("Invalid bucket_name argument: %s" % bucket_name,
                                 status_code=500) from error
    try:
        assert retention_days > 0
    except (TypeError, AssertionError) as error:
        raise utils.HandledError(f"Invalid retention_days: expected positive integer, got {error}",
                                 status_code=500) from error

    utils.Log.debug("Validate backups in bucket %s", bucket_name)

    if start_day_isoformat is None:
        start_day = TODAY - timedelta(days=retention_days)

    else:
        try:
            start_day = date.fromisoformat(start_day_isoformat)

        except (TypeError, ValueError) as error:
            raise utils.HandledError(
                f"{bucket_name}: Invalid `start_day_isoformat` argument: {error}",
                status_code=500) from error

    if start_day > TODAY:
        raise utils.HandledError(f"{bucket_name}: Wrong start day: {start_day} is in the future",
                                 status_code=500)

    expected_backups = min(retention_days, (TODAY - start_day).days + 1)
    first_expected = start_day if expected_backups < retention_days \
                               else TODAY - timedelta(days=(retention_days - 1))

    utils.Log.debug("%s: Expected %d backup(s) starting from %s",
                    bucket_name, expected_backups, first_expected)

    return expected_backups, first_expected


def _validate_backup_keys(keys: List[Dict], first_expected: date, regexp: str = None,
                          tolerance: int = None):
    previous_file_size = 0
    check_day = first_expected

    for iteration, item in enumerate(keys, start=1):
        # Validate name
        if regexp:
            utils.Log.debug("Validating key name %s against regexp %s", item["key"], regexp)
            if not match(regexp, item["key"]):
                raise utils.HandledError("Key %s doesn't match regexp %s" % (item["key"], regexp))

        # Validate LastModified timestamp
        utils.Log.debug("Validating LastModified value for key %s", item["key"])
        test, actual = check_day.isoformat()[:10], item["last_modified"].isoformat()[:10]
        if not test == actual:
            raise utils.HandledError("Wrong key %s: "
                                     "expected date %s, got %s" % (item["key"], test, actual))

        # Validate file size
        if item["size"] == 0:
            raise utils.HandledError("%s key is empty" % item["key"])

        # Validate file size delta
        if tolerance:

            if iteration > 1:
                size_diff = item["size"] - previous_file_size
                variation = round(size_diff / item["size"] * 100)

                utils.Log.debug("Found %d bytes variation (%d percent) for key %s "
                                "compared to previous backup", size_diff, variation, item["key"])

                if variation > tolerance:
                    raise utils.HandledError(
                        "Size difference compared to previous backup for key %s "
                        "above threshold of %d percent" % (item["key"], tolerance))

        previous_file_size = item["size"]
        check_day += timedelta(days=1)


def _check_bucket_validity(bucket_name: str, retention_days: int,
                           regexp: str = None,
                           start_day_isoformat: str = None,
                           tolerance: int = None) -> str:
    expected_backups, first_expected = _get_expected_values(bucket_name,
                                                            retention_days,
                                                            start_day_isoformat)

    content = [{"last_modified": item["LastModified"], "size": item["Size"], "key": item["Key"]}
               for item in aws.list_bucket(bucket_name=bucket_name)]

    if len(content) < expected_backups:
        raise utils.HandledError("%s: Invalid backups number. Expected at least %d, got %d" % (
            bucket_name, expected_backups, len(content)))

    elif len(content) > expected_backups:
        diff = len(content) - expected_backups
        if diff > 2:
            raise utils.HandledError("%s: Invalid backups number. Expected at most %d, got %d" % (
                bucket_name, expected_backups + 2, len(content)))

        utils.Log.info("%s: Ignoring oldest %d key(s): %s", bucket_name, diff, content[:diff])
        content = content[diff:]

    _validate_backup_keys(keys=content, first_expected=first_expected,
                          regexp=regexp, tolerance=tolerance)

    return f"{bucket_name}: OK"


def check_backup_buckets(_: utils.LambdaEvent) -> List[str]:
    """Scan for S3 backup bucket config in BUCKETS_TO_MONITOR env var and run checks on content.

    BUCKETS_TO_MONITOR is a ;-separated string in the format
        <bucket_name>,<retention_days>,<regexp>,<start_day_isoformat>,<tolerance>;<bucket_name>...

    where `bucket_name_x` is the S3 bucket name
    `retention_days` is an int with the max amount of days for any backup to be considered valid.
        Check will also fail if the bucket contains more than `retention_days + 1` keys. The + 1
        is because the way S3 lifecycle polices remove expired keys is non deterministic, so there
        might be moments during the day when the actual amount of keys eccedes of 1 the expected
        value.
    `regexp` is a regular expression to be used to match the bucket keys, use NoRegexp to disable
    `start_day_isoformat` is the date in iso format of the first backup ever (needed for new
        buckets only), use NoStartDay to disable
    `tolerance` is an int with the the maximum expected change in file size compared to the
        previous backup, i.e. the check will fail if the size of today's backup is
        <tolerance percent> bigger or smaller than yesterday backup, use NoTolerance to disable
    """
    configs = []
    output = []
    errors = False

    for config in env["BUCKETS_TO_MONITOR"].split(";"):
        bucket_name, retention_days, regexp, start_day_isoformat, tolerance = config.split(",")
        configs.append([
            bucket_name,
            int(retention_days),
            None if regexp == "NoRegexp" else regexp,
            None if start_day_isoformat == "NoStartDay" else start_day_isoformat,
            None if tolerance == "NoTolerance" else int(tolerance)
        ])

    futures = utils.helpers.exec_in_thread_and_wait(((_check_bucket_validity, config)
                                                     for config in configs), False)

    for future in futures.done:
        try:
            output.append(future.result())

        except utils.HandledError as error:
            output.append(str(error))
            errors = True

    if errors:
        aws.invoke_lambda(
            name=env["LAMBDA_NOTIFICATIONS"],
            payload={
                "title": "backups_monitor: errors",
                "payload": str(output),
            })

    return output


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="backups_monitor",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=check_backup_buckets,
    ).response
