# pylint: disable=protected-access
from datetime import date, datetime, timedelta
from unittest.mock import patch
from dateutil.tz import tzutc
import pytest

from stacks.backups_monitor.lambdas import backups_monitor as monitor
from utils import HandledError

TODAY = date.today()

@pytest.mark.parametrize(
    "source, expected",
    [
        [("bogus-bucket", 15), (15, TODAY - timedelta(days=14))],
        [("bogus-bucket", 100), (100, TODAY - timedelta(days=99))],
        [("bogus-bucket", 1), (1, TODAY)],
        [("bogus-bucket", 15, TODAY.isoformat()), (1, TODAY)],
        [("bogus-bucket", 15, (TODAY - timedelta(days=1)).isoformat()),
         (2, TODAY - timedelta(days=1))],
    ]
)
def test_get_expected_values(source, expected):
    assert monitor._get_expected_values(*source) == expected


@pytest.mark.parametrize(
    "source, error_message",
    [
        [(None, 15), "Invalid bucket_name argument"],
        [("some-bucket", 0), "Invalid retention_days: expected positive integer"],
        [("some-bucket", None), "Invalid retention_days: expected positive integer"],
        [("some-bucket", 1, (TODAY + timedelta(days=1)).isoformat()), "Wrong start day"],
        [("some-bucket", 1, TODAY), "Invalid `start_day_isoformat` argument"],
    ]
)
def test_get_expected_values_throws(source, error_message):
    with pytest.raises(HandledError) as error:
        monitor._get_expected_values(*source)

    assert error.match(error_message)
    assert error.value.status_code == 500


def test_validate_backup_keys():
    keys = [
        {
            "key": "backup-file-2020-08-09",
            "last_modified": datetime(2020, 8, 9, 0, 0, 10, tzinfo=tzutc()),
            "size": 5624262507
        },
        {
            "key": "backup-file-2020-08-10",
            "last_modified": datetime(2020, 8, 10, 0, 0, 10, tzinfo=tzutc()),
            "size": 5641424772
        },
        {
            "key": "backup-file-2020-08-11",
            "last_modified": datetime(2020, 8, 11, 0, 0, 9, tzinfo=tzutc()),
            "size": 5759263075
        },
    ]
    assert monitor._validate_backup_keys(keys=keys,
                                         first_expected=date.fromisoformat("2020-08-09"),
                                         regexp=r"backup-file-\d{4}-\d{2}-\d{2}$",
                                         tolerance=2) is None

@pytest.mark.parametrize(
    "key, error_message",
    [
        ({
            "key": "backup-file-2020-08-09.wrong-name",
            "last_modified": datetime(2020, 8, 9, 0, 0, 10, tzinfo=tzutc()),
            "size": 5624262507
        }, "Key backup-file-2020-08-09.wrong-name doesn't match regexp"),
        ({
            "key": "backup-file-2020-08-10",
            "last_modified": datetime(2020, 8, 9, 0, 0, 10, tzinfo=tzutc()),
            "size": 0
        }, "backup-file-2020-08-10 key is empty"),
        ({
            "key": "backup-file-2020-08-11",
            "last_modified": datetime(2020, 8, 10, 0, 0, 9, tzinfo=tzutc()),
            "size": 5759263075
        }, "Wrong key backup-file-2020-08-11: expected date 2020-08-09, got 2020-08-10"),
    ]
)
def test_validate_backup_keys_throws(key, error_message):
    with pytest.raises(HandledError) as error:
        monitor._validate_backup_keys(keys=[key],
                                      first_expected=date.fromisoformat("2020-08-09"),
                                      regexp=r"backup-file-\d{4}-\d{2}-\d{2}$")

    assert error.match(error_message)
    assert error.value.status_code == 400


@patch("utils.aws.list_bucket")
def test_check_bucket_validity(mock):
    mock.return_value = [
        {
            'Key': 'backup-1111111.tar.gz',
            'LastModified': TODAY - timedelta(days=2),
            'ETag': '"93b01e13cf2476ca8c16f0a189f0c414-671"',
            'Size': 5624262507,
            'StorageClass': 'GLACIER'
        }, {
            'Key': 'backup-1111112.tar.gz',
            'LastModified': TODAY - timedelta(days=1),
            'ETag': '"487cf444d7c41eded66bef457f996b77-673"',
            'Size': 5641424772,
            'StorageClass': 'GLACIER'
        }, {
            'Key': 'backup-1111113.tar.gz',
            'LastModified': TODAY,
            'ETag': '"545f677805ed7509d826828633163fbf-673"',
            'Size': 5641263075,
            'StorageClass': 'STANDARD'
        }
    ]
    result = monitor._check_bucket_validity("fake-bucket", retention_days=3,
                                            regexp=r"backup-\d+\.tar\.gz",
                                            start_day_isoformat="1970-01-01",
                                            tolerance=1)
    assert result == "fake-bucket: OK"
