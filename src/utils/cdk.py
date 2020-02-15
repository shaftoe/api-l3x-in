from re import match
from os import environ
from typing import (Iterable, Mapping, Union)

from aws_cdk import (
    assets,
    aws_lambda,
    aws_logs,
    core,
)


DEFAULT_TIMEOUT       = core.Duration.seconds(30)  # pylint: disable=no-value-for-parameter
DEFAULT_RUNTIME       = aws_lambda.Runtime.PYTHON_3_8
DEFAULT_LOG_RETENTION = aws_logs.RetentionDays.ONE_WEEK
DEFAULT_MEM_SIZE      = 256  # https://forums.aws.amazon.com/thread.jspa?threadID=262547 128mb sometimesis not enough
DEFAULT_ENV_REQUIRED  = ["LAMBDA_FUNCTIONS_LOG_LEVEL", "VERSION"]


def code_from_path(path: str) -> aws_lambda.Code:
    return aws_lambda.Code.from_asset(  # pylint: disable=no-value-for-parameter
        path=path.replace("-", "_"),
        follow=assets.FollowMode.ALWAYS,
        exclude=[
            "**__pycache__",
            "*.pyc",
            "cdk.py",
        ],
    )


def get_lambda(scope: core.Construct, id: str, code: Union[aws_lambda.Code, str], handler: Union[str, None] = None, layers: Iterable[aws_lambda.ILayerVersion] = [], environment: Mapping = {}) -> aws_lambda:

    _code = code if isinstance(code, aws_lambda.Code) else code_from_path(path=code)

    for required in DEFAULT_ENV_REQUIRED:
        if required not in environment:
            environment[required] = environ[required]

    return aws_lambda.Function(
            scope,
            id,
            code=_code,
            environment=validate_environment(environment),
            handler=handler,
            layers=layers,
            log_retention=DEFAULT_LOG_RETENTION,
            memory_size=DEFAULT_MEM_SIZE,
            runtime=DEFAULT_RUNTIME,
            timeout=DEFAULT_TIMEOUT,
        )


def validate_environment(environment: Mapping) -> Mapping:
    for var in environment:
        if not match(r'[a-zA-Z]([a-zA-Z0-9_])+', var):
            raise ValueError('invalid environment variable: {}'.format(var))

    return environment
