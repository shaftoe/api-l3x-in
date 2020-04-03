"""
AWS Lambda for async delivery of email messages via Mailjet service.
"""
from base64 import standard_b64encode
from os import environ as env
from typing import Mapping
import json

import utils
import utils.aws as aws
import utils.helpers as helpers
import utils.handlers as handlers


MAILJET_API_ENDPOINT = "https://api.mailjet.com/v3.1/send"


def _add_content_to_attachment(attachment: Mapping) -> Mapping:
    """Fetch bytes from S3 and add to 'Base64Content' attachment key"""
    content = aws.get_object_from_s3_bucket(key=attachment["Key"], bucket=attachment["Bucket"])

    attachment["Base64Content"] = standard_b64encode(content.read()).decode("utf-8")
    del attachment["Bucket"], attachment["Key"]


def deliver_to_mailjet(event: utils.LambdaEvent) -> str:
    """Send email message via Mailjet APIs.

    :param event:
      - may have "mail_to" email address key (use MAILJET_DEFAULT_TO_ADDRESS from env if not)
      - may have "custom_id" key (for internal Mailjet use)
      - may have "subject" key to be used as email subject
      - may have "text" key to be used as text content
      - may have "attachments" key (list of attachments dict metadata). E.g:
        {
            # https://www.iana.org/assignments/media-types/application/vnd.amazon.mobi8-ebook
            "ContentType": "application/vnd.amazon.mobi8-ebook",
            "Key": <s3_key>,
            "Bucket": <s3_bucket>,
            "Filename": "article.mobi",
        }
        Actual content is downloaded from S3 bucket.

        Refer to docs for attachment format:
        https://dev.mailjet.com/email/guides/send-api-v31/#send-with-attached-files

    API docs: https://dev.mailjet.com/email/guides/send-api-v31/
    """
    utils.Log.info("Sending email message via %s", MAILJET_API_ENDPOINT)

    msg = {
        "From": {"Email":env["MAILJET_FROM_ADDRESS"]},
        "TextPart": event.get("text", "no content"),
        "To": [{"Email": event.get("mail_to", env["MAILJET_DEFAULT_TO_ADDRESS"])}],
        "CustomID": event.get("custom_id", "api-l3x-in"),
    }

    if "subject" in event:
        msg["Subject"] = event["subject"]

    utils.Log.debug("Message content: %s", msg)

    if "attachments" in event:
        msg["Attachments"] = []

        utils.Log.debug("Adding %d attachments", len(event["attachments"]))
        for att in event["attachments"]:
            _add_content_to_attachment(att)
            utils.Log.debug("Adding %s, content-type %s", att["Filename"], att["ContentType"])
            msg["Attachments"].append(att)

    return helpers.send_http_request(
        url=MAILJET_API_ENDPOINT,
        data=bytes(json.dumps({"Messages": [msg]}), encoding="utf-8"),
        headers={"Content-Type": "application/json"},
        auth={"user": env["MAILJET_API_KEY"], "pass": env["MAILJET_API_SECRET"]},
    ).text


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="send_to_pushover",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=deliver_to_mailjet,
    ).response
