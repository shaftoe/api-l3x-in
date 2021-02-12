"""Lambda send-to-kindle publisher.

Send document to Kindle service and archive Pocket article.
"""
from os import environ as env
from re import search
from uuid import uuid4
import json

import utils
import utils.aws as aws
import utils.handlers as handlers
import utils.helpers as helpers


POCKET_API_ENDPOINT = "https://getpocket.com/v3/send"


def _archive_pocket_item(item_id: int):
    """https://getpocket.com/developer/docs/v3/modify#action_archive"""
    utils.Log.info("Archive Pocket item %d", item_id)

    return helpers.send_http_request(
        url=POCKET_API_ENDPOINT,
        data={
            "access_token": env["POCKET_SECRET_TOKEN"],
            "consumer_key": env["POCKET_CONSUMER_KEY"],
            "actions": json.dumps([
                {
                    "action": "archive",
                    # NOTE: API docs are inconsistent, they say `item_id` is an integer
                    # but examples show string usage
                    "item_id": str(item_id),
                }])})


def _send_attachment_to_kindle(key: str, bucket: str, item_id: int = None) -> utils.Response:
    utils.Log.info("Send attachment to %s via %s email notification service",
                   env["KINDLE_EMAIL"], env["LAMBDA_NOTIFICATIONS"])

    extension = None
    if key.endswith(".mobi"):
        extension = "mobi"
    if key.endswith(".html"):
        extension = "html"
    if extension not in ["mobi", "html"]:
        raise utils.HandledError(
            message="Invalid document extension: must be either '.mobi' or '.html'",
            status_code=401)

    return aws.invoke_lambda(
        name=env["LAMBDA_NOTIFICATIONS"],
        payload={
            "mail_to": env["KINDLE_EMAIL"],
            "attachments": [{
                # https://www.iana.org/assignments/media-types/
                "ContentType": "application/vnd.amazon.mobi8-ebook" \
                               if extension == "mobi" else "text/html",
                "Key": key,
                "Bucket": bucket,
                "Filename": f"pocket-{item_id}.{extension}" \
                            if item_id else f"{uuid4()}.{extension}",
            }],
        },
        invoke_type="Event")


def send(event: utils.LambdaEvent) -> str:
    """Send document to Kindle."""
    # When file matches "pocket" format we're processing a Pocket item, so if everything goes
    # as expected we archive it before exiting
    match = search(r'pocket-(\d+)', event["keyName"])
    item_id = None
    if match:
        item_id = int(match.groups()[0])

    response = _send_attachment_to_kindle(key=event["keyName"],
                                          bucket=env["DOCUMENT_SRC_BUCKET"],
                                          item_id=item_id)

    if response.status_code != 200:
        raise utils.HandledError(
            message=f"Unexpected response from notifications service: {response.text}",
            status_code=response.status_code)

    if item_id:
        _archive_pocket_item(item_id)


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.S3EventHandler(
        name="pocket_publisher",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=send,
    ).response
