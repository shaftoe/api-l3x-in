import json
from os import environ as env

import utils
import utils.handlers as handlers
import utils.helpers as helpers


LAMBDA_NOTIFICATIONS = env["LAMBDA_NOTIFICATIONS"]


def contact(event: utils.LambdaEvent) -> str:
    """
    Send event payload to Notifications lambda for delivery.

    Expects these keys in event mapping:

    - source
    - name
    - email
    - description
    """
    body = event["body"]

    utils.Log.debug("Processing body payload: %s", body)

    try:
        utils.Log.debug("Loading JSON content from body")
        utils.Log.info("json.loads should be safe to use: https://stackoverflow.com/a/45483187/2274124")

        msg = """Source: {source}
Name: {name}
Mail: {email}
Desc: {description}
""".format(**json.loads(body))

    except (TypeError, json.JSONDecodeError) as error:
        raise utils.HandledError("JSON body is malformatted: %s" % error)

    except KeyError as error:
        raise utils.HandledError("Missing JSON key: %s" % error)

    utils.Log.debug("### Message content below ###")
    utils.Log.debug(msg)
    utils.Log.debug("#############################")

    return helpers.invoke_lambda(
        name=LAMBDA_NOTIFICATIONS,
        payload={
            "title": "New /contact submission received",
            "payload": msg,
        }).text


def handler(event, context) -> utils.Response:
    """Lambda entry point.

    Public HTTPS REST API entry point
    """
    router_map = {
        "POST /contact": contact,
    }

    return handlers.ApiGatewayEventHandler(name="api",
                                           event=utils.LambdaEvent(event),
                                           context=utils.LambdaContext(context),
                                           router_map=router_map,
                                           ).response
