"""Lambda pocket-to-kindle create_doc."""
from datetime import datetime
from os import environ as env
from uuid import uuid4

import utils
import utils.aws as aws
import utils.handlers as handlers
import utils.helpers as helpers


def create_doc(event: utils.LambdaEvent) -> str:
    """Build clean HTML file from URL source and store it to S3."""
    utils.Log.info("Fetch content from %s", event["url"])
    requests = helpers.import_non_stdlib_module("requests")
    response = requests.get(url=event["url"])

    if not response.status_code == 200:
        raise utils.HandledError("Error downloading %s: "
                                 "HTTP status code %d" % (event["ur"], response.status_code),
                                 status_code=response.status_code)

    utils.Log.info("Create readability-clean HTML text from %s source", event["url"])
    readability = helpers.import_non_stdlib_module("readability")

    doc = readability.Document(response.text)

    utils.Log.debug("Document title:\n%s", doc.title())
    utils.Log.debug("Document readability-cleaned content:\n%s", doc.summary())

    now = datetime.utcnow()
    file_name = f"pocket-{event['item_id']}" if "item_id" in event else uuid4()
    key_name = now.strftime(f"%Y/%m/%d/{file_name}.html")

    aws.put_object_to_s3_bucket(key=key_name, bucket=env["DOCUMENT_BUCKET"],
                                body=bytes(doc.summary(), encoding="utf-8"))

    file_url = f"s3://{env['DOCUMENT_BUCKET']}/{key_name}"

    utils.Log.info("File %s created successfully", file_url)

    return f"success: {file_url}"


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="pocket_create_doc",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=create_doc,
    ).response
