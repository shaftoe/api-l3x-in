"""Run daily mongodump process in Fargate and upload archive to S3, delete it after 7 days."""
from os import environ as env

from aws_cdk import (
    core,
    aws_ec2,
    aws_events,
    aws_events_targets,
    aws_iam,
)

from utils.cdk import (
    DEFAULT_LOG_RETENTION,
    get_bucket,
    get_fargate_cluster,
    get_fargate_container,
    get_fargate_task,
)


class MongodumperStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        bucket = get_bucket(self, f"{id}-bucket", core.Duration.days(amount=7))

        cluster, vpc = get_fargate_cluster(self, id)

        mem_limit = "512"
        task = get_fargate_task(self, id, mem_limit)
        aws_iam.Policy(
            self,
            f"{id}-bucket-policy",
            roles=[task.task_role],
            statements=[
                aws_iam.PolicyStatement(
                    actions=["s3:PutObject"],
                    resources=[f"{bucket.bucket_arn}/*"]
                ),
            ],
        )

        get_fargate_container(
            self,
            id,
            task,
            mem_limit,
            {
                'S3_BUCKET': bucket.bucket_name,
                'MONGODB_URI': env['MONGODB_URI'],
            },
        )

        cronjob = aws_events.Rule(
            self,
            f"{id}-scheduled-event",
            enabled=True,
            schedule=aws_events.Schedule.cron(minute="0", hour="0"),  # pylint: disable=no-value-for-parameter
        )
        cronjob.add_target(aws_events_targets.EcsTask(
            cluster=cluster,
            task_definition=task,
            subnet_selection=aws_ec2.SubnetSelection(subnets=vpc.public_subnets),
            security_group=aws_ec2.SecurityGroup.from_security_group_id(
                self, f'{id}-default-security-group', vpc.vpc_default_security_group),
        ))

        buglink = "https://github.com/aws/aws-cdk/issues/9233"
        core.CfnOutput(
            self, f"{id}-fixme",
            value=f"FIXME: set cronjob 'Auto assign public IP' when this is fixed: {buglink}")
