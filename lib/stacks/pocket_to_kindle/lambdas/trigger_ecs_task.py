"""AWS Lambda that triggers ECS Fargate task."""
from os import environ as env

import utils
import utils.aws as aws
import utils.handlers as handlers


def trigger_ecs(event: utils.LambdaEvent) -> str:
    """Run ECS Fargate task with containerOverrides data.

    :param event: mapping with `keyName` and `bucketName` keys
    """
    response = aws.trigger_ecs_fargate_task(
        task=env["ECS_TASK"],
        cluster=env["ECS_CLUSTER"],
        security_groups=[env["ECS_CLUSTER_SECURITY_GROUP"]],
        subnets=[env["ECS_CLUSTER_SUBNET"]],
        overrides={
            "containerOverrides": [
                {
                    "name": env["ECS_CONTAINER"],
                    "environment": [
                        {
                            "name": "EPUB_SRC_BUCKET",
                            "value": event["bucketName"],
                        },
                        {
                            "name": "EPUB_SRC_KEY",
                            "value": event["keyName"],
                        },
                        {
                            "name": "MOBI_DEST_BUCKET",
                            "value": env["MOBI_DEST_BUCKET"],
                        },
                    ],
                },
            ],
        },
    )

    return "task triggered successfully: createdAt %s" % response["tasks"][0]["createdAt"]


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.S3EventHandler(
        name="trigger_ecs_task",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=trigger_ecs,
    ).response
