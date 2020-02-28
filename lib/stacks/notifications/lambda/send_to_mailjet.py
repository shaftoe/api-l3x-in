"""
AWS Lambda for async delivery of email messages via Mailjet service.
"""
from os import environ as env
import json

import utils
import utils.helpers as helpers
import utils.handlers as handlers


MAILJET_API_ENDPOINT = "https://api.mailjet.com/v3.1/send"


def deliver_to_mailjet(event: utils.LambdaEvent) -> str:
    """Send email message via Mailjet APIs.

    :param event:
      - must have "mail_to" email address key
      - may have "custom_id" key (for internal Mailjet use)
      - may have "subject" key to be used as email subject
      - may have "attachments" key (list of attachments). Refer to docs for attachment format:
        https://dev.mailjet.com/email/guides/send-api-v31/#send-with-attached-files

    docs: https://dev.mailjet.com/email/guides/send-api-v31/
    """
    utils.Log.info("Sending email message via %s", MAILJET_API_ENDPOINT)

    msg = {
        "From": {"Email":env["MAILJET_FROM_ADDRESS"]},
        "TextPart": event.get("text", "no content"),
        "To": [{"Email": event["mail_to"]}],
        "CustomID": event.get("custom_id", "api-l3x-in"),
    }

    if "subject" in event:
        msg["Subject"] = event["subject"]

    utils.Log.debug("Message content: %s", msg)

    if "attachments" in event:
        utils.Log.debug("Adding %d attachments", len(event["attachments"]))
        for att in event["attachments"]:
            utils.Log.debug("Adding %s, content-type %s", att["Filename"], att["ContentType"])

        msg["Attachments"] = event["attachments"]

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
