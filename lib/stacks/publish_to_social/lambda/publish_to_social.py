from os import environ

import utils
import utils.handlers as handlers
import utils.helpers as helpers


SNS_TOPIC = environ["SNS_TOPIC"]


def scrape_page(url: str) -> dict:
    """Scrape title and description from webpage at `url`."""
    utils.Log.info("Scraping {}%s in search of title and description", url)
    output = {"url": url}

    # Fetch the content
    page = helpers.send_http_request(url=url, method="GET").text

    # Parse the content
    bs4 = helpers.import_non_stdlib_module("bs4")
    soup = bs4.BeautifulSoup(page, "html.parser")
    output.update({
        "title":       soup.find("title").contents[0],
        "description": soup.find("meta", {"name": "description"})["content"],
    })

    utils.Log.debug("output: {}%s", output)
    utils.Log.info("Scraping completed successfully")

    return output


def build_message(url: str, disable: list) -> str:
    """Build message from url source."""
    utils.Log.debug("Building message from source {}%s", url)

    message = scrape_page(url)
    message["disable"] = disable

    utils.Log.debug("Returning message: {}%s", message)

    return message


def publish(event: dict) -> str:
    """
    SNS message producer

    If 'message' is an event key, use message as content.
    If 'url' is an event key, ignore 'message' key and scrape web page
    at URL in event["url"] searching for:

    - url
    - title tag content
    - meta description tag content

    Deliver the content to `publish_to_social` SNS topic.

    SNS consumers are supposed to subscribe to the topic and publish the content via
    social medias' public APIs.
    """
    if "url" in event:
        utils.Log.warning("Found 'url' key in client input, ignoring other keys")

        if not event["url"].startswith("https://"):
            raise utils.HandledError("Wrong url value: '%s'" % event["url"])

        content = build_message(event["url"],
                                disable=event.get("disable", []))

    else:
        raise utils.HandledError("Missing 'url' key in payload")

    message_id = helpers.publish_to_sns_topic(
        sns_topic=SNS_TOPIC,
        subject="publish_to_social",
        content=content
    ).text

    return "messageId '{}' with content scraped " \
           "from source {} delivered successfully".format(message_id, event["url"])


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="publish_to_social",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=publish,
    ).response
