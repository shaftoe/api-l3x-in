"""AWS Lambda that retrieves unreaded articles from getpocket.com APIs"""
from os import environ as env
from re import match
from typing import (Mapping, Tuple)
import json

import utils
import utils.aws as aws
import utils.handlers as handlers
import utils.helpers as helpers


POCKET_API_ENDPOINT = "https://getpocket.com/v3/get"


def _validate_article(article):
    """Return False if article is not valid, True otherwise."""
    regexes = (
        r'^https://([a-zA-Z]+\.)?ted\.com/',
        r'^https://([a-zA-Z]+\.)?twitter\.com/',
        r'^https://([a-zA-Z]+\.)?vimeo\.com/',
        r'^https://([a-zA-Z]+\.)?youtube\.com/',
    )

    if any(map(lambda regex: match(regex, article["url"]), regexes)):
        utils.Log.info("Ignoring item_id %s, url %s", article["item_id"], article["url"])
        return False

    return True


def retrieve() -> Tuple:
    """Docs: https://getpocket.com/developer/docs/v3/retrieve"""
    articles = tuple()
    data = {
        "consumer_key": env["POCKET_CONSUMER_KEY"],
        "access_token": env["POCKET_SECRET_TOKEN"],
    }

    utils.Log.info("Fetch 'since' from storage")
    result = aws.read_log_stream(log_group=env["SINCE_LOG_GROUP"],
                                 log_stream=env["SINCE_LOG_GROUP"])

    if result:
        last_event = result[-1]

        utils.Log.debug("Deserializing CloudWatch Logs message content")
        message = json.loads(last_event["message"])

        data["since"] = message["since"]
        utils.Log.debug("Found 'since': %d", data["since"])

    utils.Log.info("Retrieve new articles from getpocket.com APIs")
    response = helpers.send_http_request(
        url=POCKET_API_ENDPOINT,
        data=data,
    ).text

    since = response["since"]
    pocket_items = response["list"]

    if pocket_items:
        articles = tuple(filter(_validate_article, (
            {
                "item_id": item_id,
                "title": item["resolved_title"],
                "url": item["resolved_url"],
                # "tags": item.get("tags", []),  TODO, waiting for Pocket support response
            }
            for item_id, item in pocket_items.items()
            if int(item["status"]) == 0)))  ## status 0: we filter out archived/to-be-deleted items

    return articles, since


def trigger_lambdas(event: utils.LambdaEvent) -> Mapping:  # pylint: disable=unused-argument
    """Trigger EPUB creator lambdas."""
    response = {"new_articles": [], "count": 0}
    articles, since = retrieve()

    if not articles:
        utils.Log.info("Found no new articles since %d, skipping 'since' storage", since)
        return response

    response["new_articles"] = [article["url"] for article in articles]
    response["count"] = len(articles)

    utils.Log.debug("Fan-out %d new article(s) to lambda %s",
                    response["count"], env["LAMBDA_PUBLISHER"])
    for article in articles:
        utils.Log.info("Triggering Lambda %s for %s", env["LAMBDA_PUBLISHER"], article)
        aws.invoke_lambda(name=env["LAMBDA_PUBLISHER"], payload=article, invoke_type="Event")

    utils.Log.info("Store new since to LogStream: %d", since)
    aws.send_event_to_logstream(
        log_group=env["SINCE_LOG_GROUP"],
        log_stream=env["SINCE_LOG_GROUP"],
        message={
            "since": since,
            "items": sorted(int(article["item_id"]) for article in articles),
        })

    return response


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="pocket_reader",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=trigger_lambdas,
    ).response
