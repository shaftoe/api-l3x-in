from os import environ as env
import json
from typing import Iterable
import urllib.parse

import utils
import utils.handlers as handlers
import utils.helpers as helpers


DEVTO_URL = "https://dev.to/"
DEVTO_PUBLISH_URL = urllib.parse.urljoin(DEVTO_URL, "api/articles")


def get_content_from_gh(url: str) -> Iterable[str, str]:
    """Fetch blog content from GitHub and inject original blog link reference."""
    raw = helpers.get_file_from_github(helpers.from_link_to_jekyll_md(url))

    index = raw.index("---\n", 1)
    front_matter = raw[4:index].strip()
    article = raw[index + 4:].strip()

    return (front_matter, article)


def post_status(content: utils.LambdaEvent) -> str:
    """Post content to dev.to api/articles endpoint

    ref: https://docs.dev.to/api/#operation/createArticle
    """
    original_ref = env["DEVTO_ORIGINAL_REF"]
    front_matter, article = get_content_from_gh(content["url"])

    if len(content["categories"]) > 4:
        utils.Log.warning("Found more than 4 categories, removing following: %s",
                          content["categories"][4:])
        content["categories"] = content["categories"][:4]

    body = f"""---
{front_matter}
canonical_url: {content["url"]}
published: true
tags: {" ,".join(content["categories"])},
---

{original_ref}

{article}"""

    data = {
        "article": {
            "title": content["title"],
            "description": content["description"],
            "body_markdown": body,
            "published": True,
            "canonical_url": content["url"],
        },
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
