from os import environ
from typing import Union
import importlib
import json
import urllib.parse


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
    Log.debug("Formatting message '{}', '{}', using template '{}'".format(message, type(message), template))
    try:
        fmt_message = template.format(**message)

    except KeyError as error:
        raise HandledError("Missing required template key "
                           "in message dictionary: {}".format(error))

    Log.debug("### Formatted message ###")
    Log.debug(fmt_message)
    Log.debug("#########################")
    Log.debug("Formatting message completed")

    return fmt_message


def import_non_stdlib_module(module: str):
    Log.debug("Importing non-stdlib module {}".format(module))

    mod = None

    try:
        mod = importlib.import_module(module)

    except ImportError as error:
        raise HandledError(message="Error importing {} module: {}".format(module, error),
                           status_code=500)

    try:
        Log.debug("Imported '{}' module version '{}'".format(module, mod.__version__))

    except AttributeError:
        Log.debug("Imported '{}' module (missing __version__)".format(module))

    return mod


def get_file_from_github(filepath: str) -> str:
    """Download file content from raw.githubusercontent.com

    Use basic auth:
    https://developer.github.com/v3/auth/#basic-authentication

    Requires GITHUB_USER and GITHUB_TOKEN env vars
    """
    requests_auth = import_non_stdlib_module("requests.auth")

    GITHUB_URL = "https://github.com"

    return send_http_request(urllib.parse.urljoin(GITHUB_URL, filepath),
                             method="GET",
                             auth = requests_auth.HTTPBasicAuth(
                                 environ["GITHUB_USER"],
                                 environ["GITHUB_TOKEN"])).text


def send_http_request(url: str, method: str="POST", data: Union[list, None]=None, headers: dict={}, auth=None) -> Response:

    # XXX: maybe reimplement using only stdlib (urllib)?

    requests = import_non_stdlib_module('requests')
    response = Response()

    Log.debug("Sending {} request to {}".format(method, url))

    if headers:
        Log.debug("Headers: {}".format(headers))

    if data:
        Log.debug("Data: {}".format(data))

    if auth:
        Log.debug("Enabling authentication: {}".format(auth))

    resp = requests.request(method=method.upper(),
                            url=url,
                            data=data,
                            headers=headers,
                            auth=auth)

    if resp.status_code == 200:
        Log.info("{} to {} successful".format(method.upper(), url))

        response.put(resp.text)
        return response

    else:
        raise HandledError(
            message="Unexpected HTTP {} response: {}".format(method.upper(),
                                                             resp.reason),
            status_code=resp.status_code)


def publish_to_sns_topic(sns_topic: str, subject: str, content: dict) -> Response:
    """
    :returns: SNS MessageId
    """
    Log.info("Sending message with subject '{}' to SNS topic {}".format(subject, sns_topic))
    Log.debug("Message: {}".format(content))

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
    """Translate page URL to Markdown file in Jekyll codebase."""

    github_path = "{}/{}/{}".format(environ["GITHUB_USER"],
                                    environ["GITHUB_PROJECT"],
                                    environ["GITHUB_BRANCH"])

    return "{}/_posts/{}".format(github_path,
                                 urllib.parse
                                 .urlsplit(link).path
                                 .lstrip("/")
                                 .replace("/", "-")
                                 .replace(".html", ".md"))
