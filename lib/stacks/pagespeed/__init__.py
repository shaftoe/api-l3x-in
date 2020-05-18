from os import environ as env
from typing import Iterable

from aws_cdk import (
    aws_dynamodb,
    aws_events,
    aws_events_targets,
    aws_lambda,
    core,
)

from utils.cdk import (
    get_lambda,
    get_layer,
)


class PageSpeedStack(core.Stack):

    # pylint: disable=redefined-builtin
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.table = aws_dynamodb.Table(
            self,
            f"{id}-table",
            partition_key=aws_dynamodb.Attribute(name="url",
                                                 type=aws_dynamodb.AttributeType.STRING),
        )

        poller = get_lambda(
            self,
            f"{id}-lambda-poller",
            code=f"lib/stacks/{id}/lambdas",
            handler="pagespeed_poller.handler",
            layers=[get_layer(self, "requests_oauthlib", id)],
            environment={
                "DYNAMODB_TABLE": self.table.table_name,
                "GOOGLE_PAGESPEED_API_KEY": env["GOOGLE_PAGESPEED_API_KEY"],
                "GOOGLE_PAGESPEED_TARGET_URLS": env["GOOGLE_PAGESPEED_TARGET_URLS"],
            })
        self.table.grant_read_write_data(poller)

        cronjob = aws_events.Rule(
            self,
            f"{id}-scheduled-event",
            enabled=True,
            schedule=aws_events.Schedule.cron(hour="6-16", minute="30"),  # pylint: disable=no-value-for-parameter
        )
        cronjob.add_target(aws_events_targets.LambdaFunction(handler=poller))
