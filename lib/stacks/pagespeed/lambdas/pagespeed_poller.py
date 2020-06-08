'''Get page speed information thanks to Google Pagespeed APIs, store in DynamoDB table.'''
from os import environ as env
from statistics import mean
from typing import Tuple

import utils
import utils.aws as aws
import utils.handlers as handlers
import utils.helpers as helpers

requests = helpers.import_non_stdlib_module("requests")  # pylint: disable=invalid-name


GOOGLE_PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def _get_average_pagespeed_score_and_timestamp(url: str) -> Tuple[float, str]:
    """Return average of audit responses from Google PageSpeed API"""
    helpers.validate_url(url)

    helpers.Log.info("Fetching data for %s from %s", url, GOOGLE_PAGESPEED_API_URL)
    response = requests.get(url=GOOGLE_PAGESPEED_API_URL, params={
        "url": url,
        "key": env["GOOGLE_PAGESPEED_API_KEY"],
    })
    response = response.json()
    helpers.Log.debug("Response content: %s", response)

    score = float(mean(val["score"]
                       for val in response["lighthouseResult"]["audits"].values()
                       if val["score"] is not None))
    timestamp = response["analysisUTCTimestamp"]

    helpers.Log.info("Found values for %s: score=%f timestamp=%s", url, score, timestamp)

    return score, timestamp


def fetch_and_store_all_pagespeed_scores(_: utils.LambdaEvent):
    """Hit Google Pagespeed APIs in parallel for each of the given urls. Store data to DynamoDB."""
    urls = env["GOOGLE_PAGESPEED_TARGET_URLS"].replace(" ", "").split(",")

    def run_job(url):
        score, timestamp = _get_average_pagespeed_score_and_timestamp(url)
        aws.update_dynamo_item(
            table_name=env["DYNAMODB_TABLE"],
            key={"url": {"S": url}},
            att_updates={
                'latest_score_value': {
                    'Value': {'N': str(score)},  # NOTE: numeric values are sent as strings to DynDB
                    'Action': 'PUT',
                },
                'latest_score_timestamp': {
                    'Value': {'S': timestamp},
                    'Action': 'PUT',
                }
            },
        )

    helpers.exec_in_thread_and_wait(*((run_job, url) for url in urls))

    utils.Log.info("All done")


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="pagespeed_poller",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=fetch_and_store_all_pagespeed_scores,
    ).response
