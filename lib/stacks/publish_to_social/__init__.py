from os import environ
from typing import Iterable


from aws_cdk import (
    aws_lambda,
    aws_lambda_destinations,
    aws_logs,
    aws_sns,
    aws_sns_subscriptions,
    core,
)

from utils.cdk import (
    get_lambda,
    code_from_path,
    DEFAULT_LOG_RETENTION,
)


class SocialPublishStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str,  # pylint: disable=redefined-builtin
                 lambda_layers: Iterable[aws_lambda.ILayerVersion], **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        topic = aws_sns.Topic(
            self,
            "topic-{}".format(id),
        )

        code = code_from_path(path='lib/stacks/{}/lambda'.format(id))

        # PUBLISH lambda
        lambda_publish_to_social = get_lambda(
            self,
            id,
            code=code,
            handler='{}.handler'.format(id.replace("-", "_")),
            layers=[
                lambda_layers["bs4"],
                lambda_layers["requests_oauthlib"],
            ],
            environment={
                'SNS_TOPIC': topic.topic_arn,
                'LAMBDA_FUNCTIONS_LOG_LEVEL': environ.get("LAMBDA_FUNCTIONS_LOG_LEVEL", "INFO"),
            },
        )
        topic.grant_publish(lambda_publish_to_social)

        # REPORT lambdas and CloudWatch resources
        report_log_group_name = "%s-reports" % id

        self.log_group = aws_logs.LogGroup(
            self,
            "%s-report-log-group" % id,
            log_group_name=report_log_group_name,
            # NOTE: no retention defined means keep data forever
        )

        create_report_lambda = get_lambda(
            self,
            "%s-create-report" % id,
            code=code,
            handler="send_report.handler",
            environment={
                "REPORT_LOG_GROUP_NAME": report_log_group_name,
            }
        )
        self.log_group.grant_write(create_report_lambda)

        # SUBSCRIBE lambdas
        social_lambdas = [social.lower()
                          for social in environ.get("LAMBDA_FUNCTIONS", "")
                          .replace(" ", "")
                          .split(",")
                          if social]

        for social in social_lambdas:
            self.log_group.add_stream(
                "%s-%s-report-log-stream" % (id, social),
                log_stream_name=social)

        def build_lambda(name):
            """Builder function for aws_lambda.Function objects."""
            name = name.lower()
            _lambda = get_lambda(
                self,
                "{}-{}".format(id, name),
                code=code,
                handler='services.{}.handler'.format(name),
                layers=[
                    lambda_layers["requests_oauthlib"],
                ],
                environment={var: value
                             for var, value in environ.items()
                             if var.startswith(name.upper())
                             or var.startswith("LAMBDA_FUNCTIONS_")
                             or var.startswith("GITHUB_")},
                on_success=aws_lambda_destinations.LambdaDestination(create_report_lambda))

            topic.add_subscription(aws_sns_subscriptions.LambdaSubscription(_lambda))


        for social in social_lambdas:
            build_lambda(name=social)
