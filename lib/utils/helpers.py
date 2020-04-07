from os import environ
from typing import (
    Iterable,
    Mapping,
    Optional,
)
import base64
import importlib
import json
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


def from_link_to_jekyll_md(link):
    """Translate URL blog article to Markdown file in Jekyll codebase."""

    return "{}/{}/contents/basedir/_posts/{}".format(environ["GITHUB_USER"],
                                                     environ["GITHUB_PROJECT"],
                                                     urllib.parse.urlsplit(link).path
                                                     .strip("/")
                                                     .replace("/", "-")
                                                     .replace(".html", ".md"))


def get_file_from_github(filepath: str) -> str:
    """Download file content from raw.githubusercontent.com

    Ref: https://developer.github.com/v3/repos/contents/#get-contents

    Use basic auth:
    https://developer.github.com/v3/auth/#basic-authentication

    Requires GITHUB_USER and GITHUB_TOKEN env vars
    """
    github_api = "https://api.github.com/"
    path = urllib.parse.urljoin(github_api, "repos/" + filepath)

    Log.info("Downloading file content from %s", path)

    resp = send_http_request(path,
                             method="GET",
                             auth={
                                 "user": environ["GITHUB_USER"],
                                 "pass": environ["GITHUB_TOKEN"],
                             })

    Log.debug("Decoding content")
    content = base64.standard_b64decode(resp.text["content"]).decode(encoding="utf-8")

    Log.debug("Returning content: %s", content)
    return content
