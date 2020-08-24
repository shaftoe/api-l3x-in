from os import environ as env

from aws_cdk import (
    core,
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_lambda,
)

from utils.cdk import get_lambda


class BackupsMonitorStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str,  # pylint: disable=redefined-builtin
                 lambda_notifications: aws_lambda.IFunction, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        function = get_lambda(
            self,
            f"{id}-lambda",
            code=f"lib/stacks/{id.replace('-', '_')}/lambdas",
            handler="backups_monitor.handler",
            environment={
                "BUCKETS_TO_MONITOR": env["BUCKETS_TO_MONITOR"],
                "LAMBDA_NOTIFICATIONS": lambda_notifications.function_name,
            })
        lambda_notifications.grant_invoke(function)

        aws_iam.Policy(
            self,
            f"{id.replace('-', '_')}-iam-policy",
            roles=[function.role],
            statements=[
                aws_iam.PolicyStatement(
                    actions=["s3:ListBucket"],
                    resources=[
                        f"arn:aws:s3:::{line.split(',')[0]}"
                        for line in env["BUCKETS_TO_MONITOR"].split(";")
                    ],
                )
            ],
        )

        cronjob = aws_events.Rule(
            self,
            f"{id}-scheduled-event",
            enabled=True,
            schedule=aws_events.Schedule.cron(minute="0", hour="6"),  # pylint: disable=no-value-for-parameter
        )
        cronjob.add_target(aws_events_targets.LambdaFunction(function))
