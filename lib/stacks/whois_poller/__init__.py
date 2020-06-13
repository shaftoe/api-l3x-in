from os import environ as env
from typing import Iterable

from aws_cdk import (
    aws_events,
    aws_events_targets,
    aws_lambda,
    core,
)

from utils.cdk import get_lambda


class WhoisStack(core.Stack):

    # pylint: disable=redefined-builtin
    def __init__(self, scope: core.Construct, id: str,
                 lambda_notifications: aws_lambda.IFunction, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        poller = get_lambda(
            self,
            f"{id}-lambda-poller",
            code=f"lib/stacks/{id}/lambdas",
            handler="whois_poller.handler",
            environment={
                "LAMBDA_NOTIFICATIONS": lambda_notifications.function_name,
                "WHOIS_DOMAINS": env["WHOIS_DOMAINS"],
                "WHOISXMLAPI_KEY": env["WHOISXMLAPI_KEY"],
            })
        lambda_notifications.grant_invoke(poller)

        cronjob = aws_events.Rule(
            self,
            f"{id}-scheduled-event",
            enabled=True,
            schedule=aws_events.Schedule.cron(hour="23", minute="30"),  # pylint: disable=no-value-for-parameter
        )
        cronjob.add_target(aws_events_targets.LambdaFunction(handler=poller))
