import urllib.parse

import utils
import utils.handlers as handlers


# https://docs.forem.com/api/#operation/createArticle
DEVTO_URL = "https://dev.to/"
DEVTO_PUBLISH_URL = urllib.parse.urljoin(DEVTO_URL, "api/articles")


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.SnsEventHandler(
        name="devto",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=lambda x: NotImplementedError(
            "APIs reject requests with '503 Bot Disallowed', "
            "waiting for support answer.")
    ).response
