#!/usr/bin/env python3
"""
Main AWS CDK app

Docs: https://docs.aws.amazon.com/cdk/api/latest/python/
"""

### Setup environment and logging
from os import environ
with open("VERSION") as f:
    environ["VERSION"] = f.read().rstrip()

from sys import stdout
print("### api-l3x-in version ", end="")
stdout.write("\033[1;31m") # Set red, ref https://stackoverflow.com/a/37340245/2274124
print(environ["VERSION"])
stdout.write("\033[0;0m") # Unset color


### Main CDK code follows
from aws_cdk import core
APP = core.App()

from stacks.api import ApiStack
from stacks.lambda_layers import LambdaLayersStack
from stacks.notifications import NotificationsStack
from stacks.publish_to_social import SocialPublishStack

LAYERS_STACK = LambdaLayersStack(
    APP,
    'lambda-layers',
    tags={
        'Managed': 'cdk',
        'Name': 'lambda-layers',
    },
)

NOTIFICATIONS_STACK = NotificationsStack(
    APP,
    'notifications',
    tags={
        'Managed': 'cdk',
        'Name': 'notifications',
    },
)

ApiStack(
    APP,
    'api',
    lambda_notifications=NOTIFICATIONS_STACK.pushover,
    tags={
        'Managed': 'cdk',
        'Name': 'api',
    },
)

SocialPublishStack(
    APP,
    'publish-to-social',
    lambda_layers=LAYERS_STACK.layers,
    tags={
        'Managed': 'cdk',
        'Name': 'publish-to-social',
    },
)

APP.synth()
