'''Get page speed information thanks to Google Pagespeed APIs, store in DynamoDB table.'''
from concurrent.futures import (ThreadPoolExecutor, wait)
from os import environ as env
from statistics import mean
from typing import (Tuple, Union)

import utils
import utils.helpers as helpers
import utils.handlers as handlers

boto3 = helpers.import_non_stdlib_module("boto3")  # pylint: disable=invalid-name
botocore = helpers.import_non_stdlib_module("botocore")  # pylint: disable=invalid-name
requests = helpers.import_non_stdlib_module("requests")  # pylint: disable=invalid-name


GOOGLE_PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def get_average_pagespeed_score_and_timestamp(url: str) -> Tuple[Union[str, float], str]:
    """Return average of audit responses from Google PageSpeed API"""
    helpers.validate_url(url)

    helpers.Log.info("Fetching data for %s from %s", url, GOOGLE_PAGESPEED_API_URL)
    response = requests.get(url=GOOGLE_PAGESPEED_API_URL, params={
        "url": url,
        "key": env["GOOGLE_PAGESPEED_API_KEY"],
    })
    response = response.json()
    helpers.Log.debug("Response content: %s", response)

    score = mean(val["score"]
                 for val in response["lighthouseResult"]["audits"].values()
                 if val["score"] is not None)
    timestamp = response["analysisUTCTimestamp"]

    helpers.Log.info("Found values for %s: score=%f timestamp=%s", url, score, timestamp)

    return score, timestamp


def store_average_pagespeed_score(client, url: str, score: float, timestamp: str = "blah"):
    """Store average from Google PageSpeed API into DynamoDB."""
    client.update_item(
        TableName=env["DYNAMODB_TABLE"],
        Key={"url": {"S": url}},
        AttributeUpdates={
            'latest_score_value': {
                'Value': {'N': str(score)},  # NOTE: numeric values are sent as strings to DynamoDB
                'Action': 'PUT',
            },
            'latest_score_timestamp': {
                'Value': {'S': timestamp},
                'Action': 'PUT',
            }
        },
    )


def fetch_and_store_all_pagespeed_scores(_: utils.LambdaEvent):
    """Hit Google Pagespeed APIs in parallel for each of the given urls. Store data to DynamoDB."""
    client = boto3.client("dynamodb")
    executor = ThreadPoolExecutor()  # by default preserves at least 5 workers for I/O bound tasks

    def run_job(_url):
        score, timestamp = get_average_pagespeed_score_and_timestamp(_url)
        store_average_pagespeed_score(client=client, url=_url, score=score, timestamp=timestamp)

    results = wait([executor.submit(run_job, url)
                    for url in env["GOOGLE_PAGESPEED_TARGET_URLS"].replace(" ", "").split(",")])

    exceptions = [future.exception() for future in results.done.union(results.not_done)]
    if any(exceptions):
        for ex in exceptions:
            utils.Log.debug("Thread throwed exception: %s", ex)
        raise utils.HandledError("Error(s) while running parallel jobs", status_code=500)

    utils.Log.info("All done")


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="pagespeed_poller",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=fetch_and_store_all_pagespeed_scores,
    ).response
