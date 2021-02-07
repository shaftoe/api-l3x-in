from types import ModuleType
from datetime import datetime
import time
import pytest

from utils import HandledError
import utils.helpers as helpers


def test_tags_from_categories():
    assert helpers.tags_from_categories([]) == ""
    assert helpers.tags_from_categories(["one"]) == "#one"
    assert helpers.tags_from_categories(["one", "two", "three"]) == "#one #two #three"


def test_import_non_stdlib_module():
    mod = helpers.import_non_stdlib_module("pytest")
    assert isinstance(mod, ModuleType)
    assert mod.__name__ == "pytest"


def test_validate_url():
    assert helpers.validate_url("http://blah/") is None
    assert helpers.validate_url("https://blah/") is None
    assert helpers.validate_url("https://blah.com/") is None
    assert helpers.validate_url("https://blah.blah.com/path") is None
    assert helpers.validate_url("file://some/path") is None


@pytest.mark.parametrize(
    "url",
    [
        "",
        "blah://",
        "http://",
        "https://",
        "https:/something",
        "https://wrong", # missing final netloc slash
    ]
)
def test_validate_url_raises(url):
    with pytest.raises(HandledError):
        helpers.validate_url(url)


def test_midnightify():
    now = datetime.utcnow()
    assert helpers.midnightify(now).day == now.day
    assert helpers.midnightify(now).hour == 0
    assert helpers.midnightify(now).minute == 0
    assert helpers.midnightify(now).second == 0
    assert helpers.midnightify(now).microsecond == 0


@pytest.mark.parametrize(
    "unixtime, microsecond, minute, hour, day, month, year",
    [
        (0, 0, 0, 0, 1, 1, 1970),
        (1597308735, 0, 52, 9, 13, 8, 2020),
    ]
)
def test_struct_to_datetime(unixtime, microsecond, minute, hour, day, month, year):
    struct = time.gmtime(unixtime)
    date = helpers.struct_to_datetime(struct)
    assert date.microsecond == microsecond
    assert date.minute == minute
    assert date.hour == hour
    assert date.day == day
    assert date.month == month
    assert date.year == year

def test_exec_in_thread_and_wait():
    function = lambda x, y: x * y
    source = [(1, 2), (2, 4), (3, 6), (4, 8), (5, 9)]
    output = [1*2, 2*4, 3*6, 4*8, 5*9]
    futures = helpers.exec_in_thread_and_wait((function, item) for item in source)
    results = set(future.result() for future in futures.done)
    assert results == set(output)

def test_exec_in_thread_and_wait_throws():
    with pytest.raises(HandledError):
        helpers.exec_in_thread_and_wait((lambda x: 1 / x, (x, )) for x in [2, 1, 0])

@pytest.mark.parametrize(
    "mail_string, parsed",
    [
        ("some noise", (None, None)),
        ("more @ noise", (None, None)),
        ("even more @noise", (None, None)),
        ("bad@email here", (None, None)),
        ("another bad@email.address here", (None, None)),
        ("some@email.com", (None, "some@email.com")),
        ("some@email.com  ", (None, "some@email.com")),
        ("  some@email.com  ", (None, "some@email.com")),
        ("Some Email  some@email.com  ", ("Some Email", "some@email.com")),
        (" Some Other Email  some-other@email.com  ", ("Some Other Email", "some-other@email.com")),
        ("  'Some Email'  some@email.com  ", ("'Some Email'", "some@email.com")),
        ("  'Some Email  some@email.com  ", ("'Some Email", "some@email.com")),
        ("  Some Email'  some@email.com  ", ("Some Email'", "some@email.com")),
        ("Someone some@email.com", ("Someone", "some@email.com")),
        ('"Someone" some.one@email.com', ('"Someone"', "some.one@email.com")),
        ("Some One some.one@a.b.c", ("Some One", "some.one@a.b.c")),
        ("Some One Else some.one.else@a.b.c", ("Some One Else", "some.one.else@a.b.c")),
        ("'Some One Else' some.one.else@a.b.c", ("'Some One Else'", "some.one.else@a.b.c")),
        ("blahBlah 123abc789@a.b", ("blahBlah", "123abc789@a.b")),
    ]
)
def test_parsed_email_address(mail_string, parsed):
    assert helpers.parsed_email_address(mail_string) == parsed
