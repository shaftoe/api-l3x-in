from os import environ as env
from typing import Iterable

from aws_cdk import (
    aws_lambda,
    core,
)

from utils.cdk import (
    get_lambda,
    code_from_path,
)


class NotificationsStack(core.Stack):

    # pylint: disable=redefined-builtin
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.pushover = get_lambda(
            self,
            "%s-lambda-pushover" % id,
            code='lib/stacks/%s/lambda' % id,
            handler="send_to_pushover.handler",
            environment={
                "PUSHOVER_TOKEN": env["PUSHOVER_TOKEN"],
                "PUSHOVER_USERKEY": env["PUSHOVER_USERKEY"],
                "LAMBDA_FUNCTIONS_LOG_LEVEL": "INFO",
            })
