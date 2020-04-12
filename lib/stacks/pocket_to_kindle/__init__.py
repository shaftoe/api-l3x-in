from os import environ as env

from aws_cdk import (
    aws_cloudtrail,
    aws_ec2,
    aws_ecs,
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

        # Lambda create_epub (and layers): build epub file and store to S3 bucket
        epub_bucket = get_bucket(self, f"{id}-epub-bucket")

        lambda_create_epub = get_lambda(
            self,
            id + "-create-epub",
            code=lambda_code,
            handler="create_epub.handler",
            environment={
                "EPUB_BUCKET": epub_bucket.bucket_name,
            },
            layers=[get_layer(self, layer_name=layer, prefix=id)
                    for layer in ("pandoc", "html2text", "requests_oauthlib")],
            timeout=core.Duration.minutes(5),  # pylint: disable=no-value-for-parameter
        )
        epub_bucket.grant_write(lambda_create_epub)

        # Lambda send_to_kindle: invoked when new MOBI dropped into S3 bucket, deliver MOBI as
        # email attachment via lambda_notifications
        mobi_bucket = get_bucket(self, f"{id}-mobi-bucket")

        lambda_send_to_kindle = get_lambda(
            self,
            id + "-send-to-kindle",
            code=lambda_code,
            handler="send_to_kindle.handler",
            environment={
                "KINDLE_EMAIL": env["KINDLE_EMAIL"],
                "LAMBDA_NOTIFICATIONS": lambda_notifications.function_name,
                "MOBI_SRC_BUCKET": mobi_bucket.bucket_name,
                "POCKET_CONSUMER_KEY": env["POCKET_CONSUMER_KEY"],
                "POCKET_SECRET_TOKEN": env["POCKET_SECRET_TOKEN"],
            }
        )
        mobi_bucket.add_event_notification(
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
                    resources=[f"{mobi_bucket.bucket_arn}/*"]
                )
            ],
        )

        # Lambda reader: fetch new articles from Pocket and fan-out trigger create_epub Lambda
        lambda_reader = get_lambda(
            self,
            id + "-reader",
            code=lambda_code,
            handler="reader.handler",
            environment={
                "LAMBDA_PUBLISHER": lambda_create_epub.function_name,
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
        lambda_create_epub.grant_invoke(lambda_reader)

        # Fargate task: run dockerized `kindlegen` to parse EPUB to MOBI,
        # triggered by trigger_ecs_task Lambda
        # https://medium.com/@piyalikamra/s3-event-based-trigger-mechanism-to-start-ecs-far-gate-tasks-without-lambda-32f57ed10b0d
        vpc = aws_ec2.Vpc(
            self,
            f"{id}-vpc",
            max_azs=1,
            # Default VPC creates a public subnet with NAT Gateway (which costs money) so we use
            # a public subnet instead. Security concerns are minimal and default Security Group
            # is sealed anyway
            subnet_configuration=[
                aws_ec2.SubnetConfiguration(
                    name=f"{id}-public-subnet",
                    subnet_type=aws_ec2.SubnetType.PUBLIC,
                )
            ],
        )
        cluster = aws_ecs.Cluster(self, f"{id}-fargate-cluster", vpc=vpc)

        mem_limit = "512"
        task = aws_ecs.TaskDefinition(
            self,
            f"{id}-fargate-task",
            compatibility=aws_ecs.Compatibility.FARGATE,
            cpu="256",
            memory_mib=mem_limit,
        )
        aws_iam.Policy(
            self,
            f"{id}-bucket-policy",
            roles=[task.task_role],
            statements=[
                aws_iam.PolicyStatement(
                    actions=["s3:GetObject"],
                    resources=[f"{epub_bucket.bucket_arn}/*"]
                ),
                aws_iam.PolicyStatement(
                    actions=["s3:PutObject"],
                    resources=[f"{mobi_bucket.bucket_arn}/*"]
                ),
            ],
        )

        container_log_group = aws_logs.LogGroup(
            self,
            f"{id}-kindlegen-container-log-group",
            log_group_name=f"/aws/ecs/{id}",
            retention=DEFAULT_LOG_RETENTION,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        container = task.add_container(
            f"{id}-kindlegen-task-container",
            image=aws_ecs.ContainerImage.from_asset(  # pylint: disable=no-value-for-parameter
                directory=f"lib/stacks/{id}/docker".replace("-", "_")),
            memory_limit_mib=int(mem_limit),
            working_directory="/tmp",
            logging=aws_ecs.LogDrivers.aws_logs(  # pylint: disable=no-value-for-parameter
                log_group=container_log_group,
                stream_prefix="kindlegen",
            ),
        )

        # Lambda trigger_ecs_task: trigger Fargate task when new EPUB file is dropped into epub_bucket
        lambda_trigger_ecs_task = get_lambda(
            self,
            f"{id}-trigger-ecs-task",
            code=lambda_code,
            handler="trigger_ecs_task.handler",
            environment={
                "ECS_CLUSTER": cluster.cluster_arn,
                "ECS_CLUSTER_SECURITY_GROUP": vpc.vpc_default_security_group,
                "ECS_CLUSTER_SUBNET": vpc.public_subnets[0].subnet_id,
                "ECS_CONTAINER": container.container_name,
                "ECS_TASK": task.task_definition_arn,
                "MOBI_DEST_BUCKET": mobi_bucket.bucket_name,
            },
        )
        epub_bucket.add_event_notification(
            event=aws_s3.EventType.OBJECT_CREATED_PUT,
            dest=aws_s3_notifications.LambdaDestination(lambda_trigger_ecs_task),
        )
        aws_iam.Policy(
            self,
            f"{id}-lambda-trigger-policy",
            roles=[lambda_trigger_ecs_task.role],
            statements=[
                aws_iam.PolicyStatement(
                    actions=["ecs:RunTask"],
                    resources=[task.task_definition_arn],
                ),
                aws_iam.PolicyStatement(
                    actions=["iam:PassRole"],
                    resources=[
                        task.execution_role.role_arn,
                        task.task_role.role_arn,
                    ],
                )
            ],
        )

        # Cloudwatch cronjob event to check for new articles every hour
        cronjob = aws_events.Rule(
            self,
            f"{id}-scheduled-event",
            enabled=True,
            schedule=aws_events.Schedule.cron(minute="0"),  # pylint: disable=no-value-for-parameter
        )
        cronjob.add_target(aws_events_targets.LambdaFunction(handler=lambda_reader))

        # NOTE: lambda_trigger_ecs_task should be replaced by Cloudtrail event notification when I figure out
        # how to do it with CDK. Ref: https://github.com/aws-samples/aws-cdk-examples/issues/254. Follows tentative
        # implementation

        # # Cloudtrail to send events to Fargate task
        # cloudtrail_bucket = get_bucket(self, f"{id}-cloudtrail-bucket",
        #                                expiration=core.Duration.days(amount=1))  # pylint: disable=no-value-for-parameter

        # cloudtrail = aws_cloudtrail.Trail(
        #     self,
        #     f"{id}-cloudtrail",
        #     bucket=cloudtrail_bucket,
        #     include_global_service_events=False,
        #     is_multi_region_trail=False,
        # )
        # # Add a filter to remove all irrelevant events beside the ones relative to epub_bucket
        # cloudtrail.add_s3_event_selector(
        #     prefixes=[f"{epub_bucket.bucket_arn}/"],
        #     include_management_events=False,
        #     read_write_type=aws_cloudtrail.ReadWriteType.WRITE_ONLY,
        # )

        # cloudtrail.on_cloud_trail_event(
        #     f"{id}-cloudtrail-s3-put-objects",
        #     # https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/CloudWatchEventsandEventPatterns.html
        #     event_pattern=aws_events.EventPattern(
        #         detail={"eventName": ["PutObject"]},
        #         resources=[epub_bucket.bucket_arn],
        #     ),
        #     target=aws_events_targets.EcsTask(
        #         cluster=cluster,
        #         task_definition=task,
        #         subnet_selection=aws_ec2.SubnetSelection(
        #             subnet_group_name=subnet_name,
        #         ),
        #         container_overrides=[
        #             aws_events_targets.ContainerOverride(
        #                 container_name=container.container_name,
        #                 environment=[
        #                     aws_events_targets.TaskEnvironmentVariable(
        #                         name="EPUB_SRC_BUCKET",
        #                         value=epub_bucket.bucket_name,
        #                     ),
        #                     aws_events_targets.TaskEnvironmentVariable(
        #                         name="EPUB_SRC_KEY",
        #                         value="$.detail.requestParameters.key", FIXME
        #                     ),
        #                     aws_events_targets.TaskEnvironmentVariable(
        #                         name="MOBI_DEST_BUCKET",
        #                         value=mobi_bucket.bucket_name,
        #                     ),
        #                 ],
        #             ),
        #         ],
        #     )
        # )
