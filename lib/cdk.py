#!/usr/bin/env python3
"""
Main AWS CDK app

Docs: https://docs.aws.amazon.com/cdk/api/latest/python/
"""
from os import environ
from sys import stdout

### Setup environment and logging
with open("VERSION") as f:
    environ["VERSION"] = f.read().rstrip()

from aws_cdk import core
from stacks.api import ApiStack
from stacks.deployer import DeployerStack
from stacks.log_report import LogReportStack
from stacks.notifications import NotificationsStack
from stacks.pagespeed import PageSpeedStack
from stacks.pocket_to_kindle import PocketToKindleStack
from stacks.publish_to_social import SocialPublishStack
from stacks.whois_poller import WhoisStack

print("### api-l3x-in version ", end="")
stdout.write("\033[1;31m") # Set red, ref https://stackoverflow.com/a/37340245/2274124
print(environ["VERSION"])
stdout.write("\033[0;0m") # Unset color


### Main CDK code follows
APP = core.App()

NOTIFICATIONS_STACK = NotificationsStack(
    APP,
    'notifications',
    tags={
        'Managed': 'cdk',
        'Name': 'notifications',
    },
)

PUBLISH_TO_SOCIAL_STACK = SocialPublishStack(
    APP,
    'publish-to-social',
    tags={
        'Managed': 'cdk',
        'Name': 'publish-to-social',
    },
)

PAGESPEED_STACK = PageSpeedStack(
    APP,
    'pagespeed',
    tags={
        'Managed': 'cdk',
        'Name': 'pagespeed',
    },
)

ApiStack(
    APP,
    'api',
    lambda_notifications=NOTIFICATIONS_STACK.pushover,
    social_log_group=PUBLISH_TO_SOCIAL_STACK.log_group,
    pagespeed_table=PAGESPEED_STACK.table,
    tags={
        'Managed': 'cdk',
        'Name': 'api',
    },
)

PocketToKindleStack(
    APP,
    'pocket-to-kindle',
    lambda_notifications=NOTIFICATIONS_STACK.mailjet,
    tags={
        'Managed': 'cdk',
        'Name': 'pocket-to-kindle',
    },
)

LogReportStack(
    APP,
    'log-report',
    lambda_notifications=NOTIFICATIONS_STACK.mailjet,
    tags={
        'Managed': 'cdk',
        'Name': 'log-report',
    },
)

WhoisStack(
    APP,
    'whois-poller',
    lambda_notifications=NOTIFICATIONS_STACK.pushover,
    tags={
        'Managed': 'cdk',
        'Name': 'whois-poller',
    },
)

DeployerStack(
    APP,
    'deployer',
    tags={
        'Managed': 'cdk',
        'Name': 'deployer',
    },
)

APP.synth()
