#!/usr/bin/env python
"""For when you inadvertently delete publish-to-social-reports LogGroup..."""
from os import environ as env
from typing import Iterable, Dict
import datetime
import utils.aws as aws


def timestamp_from_date(date: str):
    """Return date string like "Feb 17, 2020" converted to iso8601 format."""
    return datetime.datetime.strptime(date, "%b %d, %Y").isoformat() + 'Z'


def populate_logstream(articles: Iterable[Dict]):
    """Article format:
    {
        "url": "https://a.l3x.in/2020/02/17/serverless-publish-to-multiple-social-media.html",
        "MessageId": "manual",
        "title": "Automate social media status updates with AWS Lambda, SNS and CDK",
        "timestamp": "Feb 17, 2020",
    }
    """
    for social in (social.strip(" ") for social in env["LAMBDA_FUNCTIONS"].split(",")):
        for art in articles:
            aws.send_event_to_logstream(log_group="publish-to-social-reports",
                                        log_stream=social,
                                        message=art)
