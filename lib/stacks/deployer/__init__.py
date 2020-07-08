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


class DeployerStack(core.Stack):

    # pylint: disable=redefined-builtin
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.table = aws_dynamodb.Table(
            self,
            f"{id}-table",
            partition_key=aws_dynamodb.Attribute(name="url",
                                                 type=aws_dynamodb.AttributeType.STRING),
        )

        deployer = get_lambda(
            self,
            f"{id}-lambda-deployer",
            code=f"lib/stacks/{id}/lambdas",
            handler="deployer.handler",
            layers=[get_layer(self, "feedparser", id)],
            environment={
                "DEPLOYER_FEED_URLS": env["DEPLOYER_FEED_URLS"],
                "DYNAMODB_TABLE": self.table.table_name,
                "NETLIFY_HOOK": env["NETLIFY_HOOK"],
            })
        self.table.grant_read_write_data(deployer)

        cronjob = aws_events.Rule(
            self,
            f"{id}-scheduled-event",
            enabled=True,
            schedule=aws_events.Schedule.cron(hour="6-16", minute="0"),  # pylint: disable=no-value-for-parameter
        )
        cronjob.add_target(aws_events_targets.LambdaFunction(handler=deployer))
