from os import environ as env
import json
import urllib.parse

import utils
import utils.handlers as handlers
import utils.helpers as helpers


DEVTO_URL = "https://dev.to/"
DEVTO_PUBLISH_URL = urllib.parse.urljoin(DEVTO_URL, "api/articles")


def post_status(content: utils.LambdaEvent) -> str:
    """Post content to dev.to api/articles endpoint

    ref: https://docs.dev.to/api/#operation/createArticle
    """

    data = {
        "article": {
            "title": content["title"],
            "description": content["description"],
            "body_markdown":
                helpers.get_file_from_github(
                    helpers.from_link_to_jekyll_md(content["url"])),
        },
        "published": True,
        "canonical_url": content["url"],
    }

    return helpers.send_http_request(
        url=DEVTO_PUBLISH_URL,
        data=bytes(json.dumps(data), encoding="utf-8"),
        headers={
            "api-key": env["DEVTO_API_KEY"],
            "Content-Type": "application/json"}
    ).text


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.SnsEventHandler(
        name="devto",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=post_status,
    ).response
