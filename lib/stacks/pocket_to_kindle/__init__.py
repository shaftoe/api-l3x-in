from os import environ as env

from aws_cdk import (
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_lambda,
    aws_logs,
    aws_s3,
    aws_s3_notifications,
    aws_sns,
    aws_sns_subscriptions,
    core,
)

from utils.cdk import (
    DEFAULT_LOG_RETENTION,
    code_from_path,
    get_bucket,
    get_fargate_cluster,
    get_fargate_container,
    get_fargate_task,
    get_lambda,
    get_layer,
)


class PocketToKindleStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str,  # pylint: disable=redefined-builtin
                 lambda_notifications: aws_lambda.IFunction, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        # CloudWatch LogGroup and Stream to store 'since' timestamp value
        since_log_group = aws_logs.LogGroup(
            self,
            f"{id}-log-group",
            log_group_name=f"{id}-timestamps",
            retention=DEFAULT_LOG_RETENTION,
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        since_log_group.add_stream(
            f"{id}-log-stream",
            log_stream_name=since_log_group.log_group_name,
        )

        # Lambda shared code
        lambda_code = code_from_path(path=f"lib/stacks/{id}/lambdas")

        # Lambda create_doc (and layers): build document file and store to S3 bucket
        bucket = get_bucket(self, f"{id}-bucket")

        lambda_create_doc = get_lambda(
            self,
            id + "-create-document",
            code=lambda_code,
            handler="create_doc.handler",
            environment={
                "DOCUMENT_BUCKET": bucket.bucket_name,
            },
            layers=[get_layer(self, layer_name=layer, prefix=id)
                    for layer in ("readability", "requests_oauthlib")],
            timeout=core.Duration.minutes(5),  # pylint: disable=no-value-for-parameter
        )
        bucket.grant_write(lambda_create_doc)

        # Lambda send_to_kindle: invoked when new documents dropped into S3 bucket,
        # deliver document as email attachment via lambda_notifications
        lambda_send_to_kindle = get_lambda(
            self,
            id + "-send-to-kindle",
            code=lambda_code,
            handler="send_to_kindle.handler",
            environment={
                "KINDLE_EMAIL": env["KINDLE_EMAIL"],
                "LAMBDA_NOTIFICATIONS": lambda_notifications.function_name,
                "DOCUMENT_SRC_BUCKET": bucket.bucket_name,
                "POCKET_CONSUMER_KEY": env["POCKET_CONSUMER_KEY"],
                "POCKET_SECRET_TOKEN": env["POCKET_SECRET_TOKEN"],
            }
        )
        bucket.add_event_notification(
            event=aws_s3.EventType.OBJECT_CREATED_PUT,
            dest=aws_s3_notifications.LambdaDestination(lambda_send_to_kindle),
        )
        lambda_notifications.grant_invoke(lambda_send_to_kindle)
        aws_iam.Policy(
            self,
            f"{id}-mail-attachment-policy",
            roles=[lambda_notifications.role],
            statements=[
                aws_iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=[f"{bucket.bucket_arn}/*"]
                )
            ],
        )

        # Lambda reader: fetch new articles from Pocket and fan-out trigger create_doc Lambda
        lambda_reader = get_lambda(
            self,
            id + "-reader",
            code=lambda_code,
            handler="reader.handler",
            environment={
                "LAMBDA_PUBLISHER": lambda_create_doc.function_name,
                "POCKET_CONSUMER_KEY": env["POCKET_CONSUMER_KEY"],
                "POCKET_SECRET_TOKEN": env["POCKET_SECRET_TOKEN"],
                "SINCE_LOG_GROUP": since_log_group.log_group_name,
            },
        )
        since_log_group.grant(
            lambda_reader,
            "logs:GetLogEvents",
            "logs:PutLogEvents",
        )
        lambda_create_doc.grant_invoke(lambda_reader)

        # Cloudwatch cronjob event to check for new articles every hour
        cronjob = aws_events.Rule(
            self,
            f"{id}-scheduled-event",
            enabled=True,
            schedule=aws_events.Schedule.cron(minute="0"),  # pylint: disable=no-value-for-parameter
        )
        cronjob.add_target(aws_events_targets.LambdaFunction(handler=lambda_reader))
