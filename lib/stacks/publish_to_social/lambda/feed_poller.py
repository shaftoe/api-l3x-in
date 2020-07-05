from datetime import (datetime, timedelta)
from os import environ as env
import time

import utils
import utils.aws as aws
import utils.handlers as handlers
import utils.helpers as helpers


def _poll_new_posts() -> list:
    """Poll RSS/Atom feed and return new entries since yesterday at midnight."""
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)

    # Jekyll's RSS plugin adds articles dated midnight of the publishing day, so we
    # check from yesterday to today at 00:00 precisely
    yesterday_noon = helpers.midnightify(yesterday)
    today_noon = helpers.midnightify(now)

    utils.Log.info("Considering new entries from %s between '%s' and '%s'",
                   env["BLOG_FEED_URL"], yesterday_noon, now)

    feedparser = helpers.import_non_stdlib_module("feedparser")

    # Unfortunately our RSS feed doesn't support ETAG yet,
    # i.e. we need to fetch the whole feed content every time.
    utils.Log.info("Fetching content from %s", env["BLOG_FEED_URL"])
    source = feedparser.parse(env["BLOG_FEED_URL"])

    struct_to_datetime = helpers.struct_to_datetime

    new_posts = [entry.link for entry in reversed(source.entries)
                 if yesterday_noon <= struct_to_datetime(entry.published_parsed) < today_noon]

    if new_posts:
        utils.Log.info("Found %d new posts", len(new_posts))
        utils.Log.info(new_posts)
    else:
        utils.Log.info("No new posts found")

    return new_posts


def invoke_publish(_: utils.LambdaEvent):
    """Poll blog's RSS/Atom feed and trigger LAMBDA_PUBLISH for each article added yesterday."""
    posts = _poll_new_posts()

    for index, post in enumerate(posts, start=1):
        utils.Log.warning("Triggering lambda %s with payload URL %s", env["LAMBDA_PUBLISH"], post)
        aws.invoke_lambda(env["LAMBDA_PUBLISH"], payload={"url": post})
        if index < len(posts):
            time.sleep(10)  # In case of multiple posts, delay 10 seconds to allow
                            # previous one to be published


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="feed_poller",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=invoke_publish,
    ).response
