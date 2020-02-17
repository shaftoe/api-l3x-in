from os import environ as env
import json

import utils
import utils.aws as aws
import utils.handlers as handlers


def put_record_to_logstream(event: utils.LambdaEvent) -> str:
    """Put a record of source Lambda execution in LogWatch Logs."""
    log_group_name = env["REPORT_LOG_GROUP_NAME"]

    utils.Log.info("Fetching requestPayload and responsePayload")
    req, res = event["requestPayload"], event["responsePayload"]

    utils.Log.info("Fetching requestPayload content")
    sns_payload = req["Records"][0]["Sns"]

    message_id = sns_payload["MessageId"]
    message = json.loads(sns_payload["Message"])
    url, title = message["url"], message["title"]

    try:
        body = json.loads(res["body"])

    except json.JSONDecodeError as error:
        raise utils.HandledError("Failed decoding payload: %s" % error)

    name, timestamp = body["name"], body["timestamp"]

    if res["statusCode"] != 200:
        raise utils.HandledError("Source lambda '%s' failed with status code %d, "
                                 "ignoring report" % (name, res["statusCode"]))

    return aws.send_event_to_logstream(log_group=log_group_name,
                                       log_stream=name,
                                       message={
                                           "url": url,
                                           "MessageId": message_id,
                                           "title": title,
                                           "timestamp": timestamp,
                                       })


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="publish_to_social",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=put_record_to_logstream,
    ).response
