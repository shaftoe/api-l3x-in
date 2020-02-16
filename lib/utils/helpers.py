from os import environ
from typing import Union, Mapping
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


def format_message(message: dict, template: str) -> str:
    """
    :param message: a dict with keys used for template formatting
    :param template: a str used as template formatter
    """
    Log.debug("Formatting message '%s', '%s', using template '%s'" % (message, type(message), template))
    try:
        fmt_message = template.format(**message)

    except KeyError as error:
        raise HandledError("Missing required template key "
                           "in message dictionary: %s" % error)

    Log.debug("### Formatted message ###")
    Log.debug(fmt_message)
    Log.debug("Formatting message completed")

    return fmt_message


def import_non_stdlib_module(module: str):
    Log.debug("Importing non-stdlib module %s" % module)

    mod = None

    try:
        mod = importlib.import_module(module)

    except ImportError as error:
        raise HandledError(message="Error importing {} module: {}".format(module, error),
                           status_code=500)

    try:
        Log.debug("Imported '%s' module version '%s'" % (module, mod.__version__))

    except AttributeError:
        Log.debug("Imported '%s' module (missing __version__)" % module)

    return mod


def validate_url(url: str):
    """
    :throws HandledError:

    FIXME: improve validation for netloc and path, ref: https://stackoverflow.com/a/38020041/2274124
    """
    Log.debug("Validating URL string %s" % url)
    result = urllib.parse.urlparse(url)

    if not all([result.scheme in ["file", "http", "https"], result.netloc, result.path]):
        raise HandledError(message="URL invalid: {}".format(url))


def send_http_request(url: str, method: str="POST", data: Union[list, None]=None, headers: Mapping={}, auth: Mapping={}) -> Response:

    validate_url(url)

    method = method.upper()

    Log.info("Handling HTTP %s request to %s" % (method, url))

    if headers:
        Log.debug("Headers: %s" % headers)

    if data:
        Log.debug("Data: %s" % data)

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
        Log.debug("Enabling Basic Authentication: %s" % auth)

        auth_string = '{}:{}'.format(auth["user"], auth["pass"])
        base64_string = base64.standard_b64encode(auth_string.encode('utf-8'))
        auth_header = "Basic {}".format(base64_string.decode('utf-8'))
        Log.debug("Authorization header: %s" % auth_header)

        request.add_header("Authorization", auth_header)

    try:
        Log.debug("Triggering HTTP %s request" % method)
        res = urllib.request.urlopen(request)
        Log.debug("HTTP %s request successful" % method)

    except urllib.error.HTTPError as error:
        raise HandledError(
            message="Unexpected HTTP {} response: {}".format(method,
                                                             error.reason),
            status_code=error.code)

    content = res.read()

    try:
        Log.debug("Decoding content with utf-8")
        content = content.decode("utf-8")

    except Exception as error:
        Log.warning("Failed decoding content bytes into utf-8")

    try:
        Log.debug("Deserializing JSON content")
        content = json.loads(content)

    except json.JSONDecodeError as error:
        Log.warning("Deserialization failed, using 'content' as is")

    response = Response()
    response.put(content)

    Log.info("Handling of %s %s successful" % (method, url))
    return response


def invoke_lambda(name: str, payload: dict, invoke_type: str = "RequestResponse") -> Response:
    """Trigger AWS Lambda execution."""

    response = Response()

    boto3 = import_non_stdlib_module("boto3")
    lambda_client = boto3.client("lambda")

    Log.debug("Invoking lambda %s", name)

    lambda_resp = lambda_client.invoke(
        FunctionName=name,
        InvocationType=invoke_type,
        Payload=json.dumps(payload))

    Log.debug("Lambda invocation succesful")

    Log.debug("Deserializing Lambda response Payload")
    lambda_payload = json.load(lambda_resp["Payload"])

    if not lambda_resp["StatusCode"] == 200:
        raise HandledError(message=lambda_payload,
                           status_code=lambda_resp["StatusCode"])

    Log.debug("Return response with payload %s", lambda_payload)

    response.put(lambda_payload)
    return response


def publish_to_sns_topic(sns_topic: str, subject: str, content: dict) -> Response:
    """
    :returns: SNS MessageId
    """
    Log.info("Sending message with subject '%s' to SNS topic %s" % (subject, sns_topic))
    Log.debug("Message: %s" % content)

    boto3 = import_non_stdlib_module("boto3")
    sns = boto3.client("sns")

    sns_response = sns.publish(
        TopicArn=sns_topic,
        Message=json.dumps(content),
        Subject=subject,
    )

    try:
        response = Response()
        response.put(sns_response["MessageId"])
        return response

    except KeyError:  # Hard exit to ensure Lambda is requeued for retrial
        raise SystemExit("Missing MessageId in SNS response")


def from_link_to_jekyll_md(link):
    """Translate URL blog article to Markdown file in Jekyll codebase."""

    return "{}/{}/contents/_posts/{}".format(environ["GITHUB_USER"],
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
    GITHUB_API = "https://api.github.com/"

    resp = send_http_request(urllib.parse.urljoin(GITHUB_API, "repos/" + filepath),
                             method="GET",
                             auth={
                                 "user": environ["GITHUB_USER"],
                                 "pass": environ["GITHUB_TOKEN"],
                             })

    return base64.standard_b64decode(resp.text["content"])
