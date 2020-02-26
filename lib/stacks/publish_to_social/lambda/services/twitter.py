from os import environ
import urllib.parse

import utils
import utils.oauth as oauth
import utils.handlers as handlers
import utils.helpers as helpers


TWITTER_URL = "https://api.twitter.com/"
TWITTER_STATUS_URL = urllib.parse.urljoin(TWITTER_URL, "1.1/statuses/update.json")


def post_status(message) -> str:
    """Post message to Twitter statuses/update APIs

    # pylint: disable=line-too-long
    ref: https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/post-statuses-update
    """
    status = f"""New blog post:

"{message["title"]}"

{helpers.tags_from_categories(message["categories"])}

{message["url"]}"""

    return oauth.post_request_to_v1_endpoint(
        url=TWITTER_STATUS_URL,
        client_key=environ["TWITTER_OAUTH_CONSUMER_KEY"],
        client_secret=environ["TWITTER_OAUTH_CONSUMER_SECRET"],
        resource_owner_key=environ["TWITTER_OAUTH_ACCESS_TOKEN"],
        resource_owner_secret=environ["TWITTER_OAUTH_ACCESS_TOKEN_SECRET"],
        post_data={'status': status}).text


def handler(event, context) -> utils.Response:
    """lambda entry point."""
    return handlers.SnsEventHandler(
        name="twitter",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=post_status,
    ).response
