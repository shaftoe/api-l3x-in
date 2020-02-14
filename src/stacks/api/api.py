import json
import logging
from typing import Callable
from os import environ as env

import utils
import utils.handlers as handlers
import utils.helpers as helpers


PUSHOVER_API_ENDPOINT = "https://api.pushover.net/1/messages.json"


def _send_msg_to_pushover(title: str, payload: str) -> str:
    """Send payload as message to Pushover API."""
    utils.Log.info("Delivering message via Pushover")

    data = {
        "token": env["PUSHOVER_TOKEN"],
        "user": env["PUSHOVER_USERKEY"],
        "message": payload,
        "title": title,
    }

    return helpers.send_http_request(url=PUSHOVER_API_ENDPOINT,
                                     data=data,
                                     method="POST").text


def contact(event: utils.LambdaEvent) -> str:
    """
    Send event payload to Pushover for delivery.

    Expects these keys in event mapping:

    - source
    - name
    - email
    - description
    """
    body = event["body"]

    utils.Log.debug("Processing body payload: %s" % body)

    try:
        utils.Log.debug("Loading JSON content from body")
        utils.Log.info("json.loads should be safe to use: https://stackoverflow.com/a/45483187/2274124")

        msg = """Source: {source}
Name: {name}
Mail: {email}
Desc: {description}
""".format(**json.loads(body))

    except (TypeError, json.JSONDecodeError) as error:
        raise utils.HandledError("JSON body is malformatted: {}".format(error))

    except KeyError as error:
        raise utils.HandledError("Missing JSON key: {}".format(error))

    utils.Log.debug("### Message content below ###")
    utils.Log.debug(msg)
    utils.Log.debug("#############################")

    return _send_msg_to_pushover(title="New /contact submission received",
                                 payload=msg)


def router(event: utils.LambdaEvent) -> str:
    """Call routed action.

    XXX: evaluate relocation to "utils" module for reusal
    """

    ACTIONS_MAP = {
        "POST /contact": contact,
    }

    return ACTIONS_MAP.get(event["route"],
                           lambda x: utils.HandledError(
                               message="{} not found".format(x["route"]),
                               status_code=404)) \
                            (event)


def handler(event, context) -> utils.Response:
    """Lambda entry point.

    Public HTTPS REST API entry point
    """
    return handlers.ApiGatewayEventHandler(name="api",
                                           event=utils.LambdaEvent(event),
                                           context=utils.LambdaContext(context),
                                           action=router,
                                           ).response
