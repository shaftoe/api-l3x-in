from os import environ
import urllib.parse

import utils
import utils.oauth as oauth
import utils.handlers as handlers
import utils.helpers as helpers


def post_status(event: utils.LambdaEvent) -> str:
    """Post status update to Mastodon

    Docs: https://docs.joinmastodon.org/methods/statuses/
    """
    utils.Log.info("Posting status to Mastodon")

    status = f"""New blog post:

{event["description"]}

{helpers.tags_from_categories(event["categories"])}

{event["url"]}"""

    return oauth.post_request_to_v2_endpoint(
        token_url=None,
        publish_url=urllib.parse.urljoin(environ["MASTODON_URL"], "api/v1/statuses"),
        client_id=environ["MASTODON_CLIENT_KEY"],
        client_secret=environ["MASTODON_CLIENT_SECRET"],
        auth_token=environ["MASTODON_ACCESS_TOKEN"],
        scope=["write:statuses"],
        data={"status": status}).text


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.SnsEventHandler(
        name="mastodon",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=post_status,
    ).response
