from os import environ as env
from typing import Iterable

from aws_cdk import (
    aws_events,
    aws_events_targets,
    aws_lambda,
    aws_iam,
    core,
)

from utils.cdk import get_lambda


class LogReportStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str,  # pylint: disable=redefined-builtin
                 lambda_notifications: aws_lambda.IFunction, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        _lambda = get_lambda(
            self,
            f"{id}-lambda",
            code=f"lib/stacks/{id}/lambdas",
            handler="send_report.handler",
            environment={
                "LAMBDA_FUNCTIONS_LOG_LEVEL": "INFO",
                "LAMBDA_NOTIFICATIONS": lambda_notifications.function_name,
            },
            timeout=core.Duration.minutes(15),  # pylint: disable=no-value-for-parameter
        )

        lambda_notifications.grant_invoke(_lambda)

        aws_iam.Policy(
            self,
            f"{id}-iam-policy-logs",
            roles=[_lambda.role],
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "logs:DeleteLogStream",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams",
                        "logs:GetLogEvents",
                    ],
                    resources=[f"arn:aws:logs:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:*"],
                )
            ],
        )

        cronjob = aws_events.Rule(
            self,
            f"{id}-scheduled-event",
            enabled=True,
            schedule=aws_events.Schedule.cron(hour="0", minute="0"),  # pylint: disable=no-value-for-parameter
        )
        cronjob.add_target(aws_events_targets.LambdaFunction(handler=_lambda))
