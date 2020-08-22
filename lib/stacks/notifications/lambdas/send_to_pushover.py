from os import environ as env
from re import match

import utils
import utils.helpers as helpers
import utils.handlers as handlers


PUSHOVER_API_ENDPOINT = "https://api.pushover.net/1/messages.json"


def send(event: utils.LambdaEvent) -> str:
    """Send payload as message to Pushover API."""
    utils.Log.info("Delivering message via Pushover")

    title = event["title"]
    payload = event["payload"]
    token = env["PUSHOVER_TOKEN"]
    user = env["PUSHOVER_USERKEY"]

    for string in token, user:
        try:
            assert len(string) == 30
            assert match(r"[a-z0-9]+", string)
        except AssertionError as error:
            raise utils.HandledError(f"Pushover string token malformed: {string}",
                                     status_code=500) from error

    data = {
        "token": token,
        "user": user,
        "message": payload,
        "title": title,
    }

    resp = helpers.send_http_request(url=PUSHOVER_API_ENDPOINT,
                                     data=data).text

    try:
        status = resp["status"]
        assert status == 1
        req_id = resp["request"]
        return "Message sent to Pushover successful (request '%s')" % req_id

    except Exception as error:
        raise utils.HandledError("Unexpected response from Pushover: %s" % error,
                                 status_code=500)


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="send_to_pushover",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=send,
    ).response
