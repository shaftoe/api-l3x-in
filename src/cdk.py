#!/usr/bin/env python3
"""
Main AWS CDK app

Docs: https://docs.aws.amazon.com/cdk/api/latest/python/
"""

from aws_cdk import core

from stacks.api import ApiStack
from stacks.lambda_layers import LambdaLayersStack
from stacks.publish_to_social import SocialPublishStack

app = core.App()

layers_stack = LambdaLayersStack(
  app,
  'lambda-layers',
  tags={
    'Managed': 'cdk',
    'Name': 'lambda-layers',
  },
)

ApiStack(
  app,
  'api',
  lambda_layers=layers_stack.layers,
  tags={
    'Managed': 'cdk',
    'Name': 'api',
  },
)

SocialPublishStack(
  app,
  'publish-to-social',
  lambda_layers=layers_stack.layers,
  tags={
    'Managed': 'cdk',
    'Name': 'publish-to-social',
  },
)

app.synth()
