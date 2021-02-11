from concurrent.futures import (
    Future,
    ThreadPoolExecutor,
    wait,
)
from datetime import datetime
from re import search
from typing import (
    Iterable,
    List,
    Mapping,
    Optional,
    Callable,
    Tuple,
)
import base64
import importlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from . import (
    HandledError,
    Log,
    Response,
)


def tags_from_categories(categories: Iterable) -> str:
    """Return a #tag1 #tag2 kind of string from input list."""
    return " ".join("#%s" % cat for cat in categories)


def import_non_stdlib_module(module: str):
    Log.debug("Importing non-stdlib module %s", module)

    mod = None

    try:
        mod = importlib.import_module(module)

    except ImportError as error:
        raise HandledError(message="Error importing %s module: %s" % (module, error),
                           status_code=500)

    try:
        Log.debug("Imported '%s' module version '%s'", module, str(mod.__version__))

    except AttributeError:
        Log.debug("Imported '%s' module (missing __version__)", module)

    return mod


def validate_url(url: str):
    """
    :throws HandledError:

    FIXME: improve validation for netloc and path, ref: https://stackoverflow.com/a/38020041/2274124
    """
    Log.debug("Validating URL string %s", url)
    result = urllib.parse.urlparse(url)

    if not all([result.scheme in ["file", "http", "https"], result.netloc, result.path]):
        raise HandledError(message="URL invalid: %s" % url)

# pylint: disable=unsubscriptable-object
def send_http_request(url: str, method: str = "POST", data: Optional[Mapping] = None,
                      headers: Optional[Mapping] = None,
                      auth: Optional[Mapping] = None) -> Response:

    validate_url(url)

    method = method.upper()

    Log.info("Handling HTTP %s request to %s", method, url)

    if headers:
        Log.debug("Headers: %s", headers)
    else:
        headers = {}

    if data:
        Log.debug("Data: %s", data)

        if method == "GET":
            raise HandledError("Invalid input: GET does not support 'data'")

        # https://docs.python.org/3/library/urllib.request.html#urllib.request.Request
        if not isinstance(data, bytes):
            Log.debug("URL-Encoding data to UTF-8")
            data = bytes(urllib.parse.urlencode(data), encoding="utf-8")

    request = urllib.request.Request(url=url,
                                     data=data,
                                     headers=headers)

    if auth:
        # ref: https://stackoverflow.com/a/47200746/2274124
        Log.debug("Enabling Basic Authentication: %s", auth)

        auth_string = '%s:%s' % (auth["user"], auth["pass"])
        base64_string = base64.standard_b64encode(auth_string.encode('utf-8'))
        auth_header = "Basic %s" % base64_string.decode('utf-8')
        Log.debug("Authorization header: %s", auth_header)

        request.add_header("Authorization", auth_header)

    try:
        Log.debug("Triggering HTTP %s request", method)
        res = urllib.request.urlopen(request)
        Log.debug("HTTP %s request successful", method)

    except urllib.error.HTTPError as error:
        raise HandledError(
            message="Unexpected HTTP {} response: {}".format(method,
                                                             error.reason),
            status_code=error.code)

    content = res.read()

    try:
        Log.debug("Decoding content with utf-8")
        content = content.decode("utf-8")

    except Exception as error:  # pylint: disable=broad-except
        Log.debug("Failed decoding content bytes into utf-8")

    try:
        Log.debug("Deserializing JSON content")
        content = json.loads(content)

    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as error:
        Log.debug("Deserialization failed, using 'content' as is")

    response = Response()
    response.put(content)

    Log.debug("Content: %s", content)
    Log.info("Handling of %s %s successful", method, url)
    return response


def midnightify(date: datetime) -> datetime:
    """Return midnightified datetime."""
    return date.replace(hour=0, minute=0, second=0, microsecond=0)


def exec_in_thread_and_wait(jobs: Tuple[Callable, Tuple],
                            throw: Optional[bool] = True) -> List[Future]:
    """Execute callables in a ThreadPoolExecutor and wait. Return list of Future objects."""
    executor = ThreadPoolExecutor()  # by default preserves at least 5 workers for I/O bound tasks

    futures = wait([executor.submit(job, *args) for job, args in jobs])

    if throw:
        exceptions = [future.exception() for future in futures.done.union(futures.not_done)]
        if any(exceptions):
            for thread_number, ex in enumerate(exceptions):
                if ex:
                    Log.error("Thread %d throwed exception: %s", thread_number, ex)
            raise HandledError("Error(s) while running parallel jobs", status_code=500)

    return futures


def struct_to_datetime(struct: time.struct_time) -> datetime:
    """Return datetime from time.struc_time."""
    return datetime.fromtimestamp(time.mktime(struct))


def parsed_email_address(mail_string: str) -> Tuple[str, str]:
    """Parse MAIL_FROM-like string and return tuple with name string and email address."""
    matches = [None, None]
    # email regex from https://emailregex.com/
    match = search(r'((.*) )?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+) *$', mail_string)

    if match:
        Log.debug("String input '%s' matches regexp", mail_string)
        matches = list(match.groups()[1:])

        if matches[0]:
            if search(r"^ +$", matches[0]):
                matches[0] = None
            else:
                matches[0] = matches[0].lstrip(" ").rstrip(" ")

        matches[1] = matches[1].rstrip(" ")
        Log.debug("Found content: %s", matches)

    else:
        Log.debug("No matching email address string found")

    return tuple(matches)
