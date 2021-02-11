from re import match
from os import environ
from typing import (Iterable, Mapping, Union, Optional, Tuple)

from aws_cdk import (
    assets,
    aws_ec2,
    aws_ecs,
    aws_s3,
    aws_lambda,
    aws_logs,
    core,
)


DEFAULT_ENV_REQUIRED = ["LAMBDA_FUNCTIONS_LOG_LEVEL", "VERSION"]
DEFAULT_S3_EXPIRATION = core.Duration.days(amount=1)  # pylint: disable=no-value-for-parameter
DEFAULT_LOG_RETENTION = aws_logs.RetentionDays.ONE_WEEK
DEFAULT_RUNTIME = aws_lambda.Runtime.PYTHON_3_8
DEFAULT_TIMEOUT = core.Duration.seconds(30)  # pylint: disable=no-value-for-parameter

# default of 128mb might not be enough: https://forums.aws.amazon.com/thread.jspa?threadID=262547
DEFAULT_MEM_SIZE = 256


def code_from_path(path: str) -> aws_lambda.Code:
    return aws_lambda.Code.from_asset(  # pylint: disable=no-value-for-parameter
        path=path.replace("-", "_"),
        follow=core.SymlinkFollowMode.ALWAYS,
        exclude=[
            "**__pycache__",
            "*.pyc",
            "cdk.py",
        ],
    )

# pylint: disable=unsubscriptable-object
def get_lambda(scope: core.Construct, id: str,  # pylint: disable=redefined-builtin,invalid-name
               code: Union[aws_lambda.Code, str],
               handler: str,
               timeout: core.Duration = DEFAULT_TIMEOUT,
               layers: Optional[Iterable[aws_lambda.ILayerVersion]] = None,
               environment: Optional[Mapping] = None,
               on_success: Optional[aws_lambda.IDestination] = None,
               retry_attempts: Optional[int] = None) -> aws_lambda:

    _code = code if isinstance(code, aws_lambda.Code) else code_from_path(path=code)

    if not environment:
        environment = {}

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
        timeout=timeout,
        on_success=on_success,
        retry_attempts=retry_attempts,
    )


def get_layer(scope: core.Construct,
              layer_name: str,
              prefix: str,
              compatible_runtimes: Optional[Iterable[aws_lambda.Runtime]] = None,
              description: str = None) -> aws_lambda.LayerVersion:

    if not compatible_runtimes:
        compatible_runtimes = [DEFAULT_RUNTIME]

    if not description:
        description = f"Add {layer_name} dependency"

    return aws_lambda.LayerVersion(
        scope,
        f"{prefix}-lambda-layer-python3-{layer_name}",
        code=code_from_path(path=f"lib/layers/{layer_name}"),
        compatible_runtimes=compatible_runtimes,
        license="Apache-2.0",
        description=description,
    )


def get_bucket(scope: core.Construct, construct_id: str,
               expiration: Optional[core.Duration] = DEFAULT_S3_EXPIRATION) -> aws_s3.IBucket:
    return aws_s3.Bucket(
        scope,
        construct_id,
        lifecycle_rules=[aws_s3.LifecycleRule(expiration=expiration)],
        removal_policy=core.RemovalPolicy.DESTROY,
    )


def validate_environment(environment: Mapping) -> Mapping:
    for var in environment:
        if not match(r'[a-zA-Z]([a-zA-Z0-9_])+', var):
            raise ValueError('invalid environment variable: {}'.format(var))

    return environment


def get_fargate_cluster(scope: core.Construct, construct_id: str) -> Tuple[aws_ecs.ICluster, aws_ec2.IVpc]:
    vpc = aws_ec2.Vpc(
        scope,
        f"{construct_id}-vpc",
        max_azs=1,
        # Default VPC creates a public subnet with NAT Gateway (which costs money) so we use
        # a public subnet instead. Security concerns are minimal and default Security Group
        # is sealed anyway
        subnet_configuration=[
            aws_ec2.SubnetConfiguration(
                name=f"{construct_id}-public-subnet",
                subnet_type=aws_ec2.SubnetType.PUBLIC,
            )
        ],
    )
    cluster = aws_ecs.Cluster(scope, f"{construct_id}-fargate-cluster", vpc=vpc)

    return cluster, vpc


def get_fargate_task(scope: core.Construct, construct_id: str, mem_limit: str) -> aws_ecs.ITaskDefinition:
    return aws_ecs.TaskDefinition(
        scope,
        f"{construct_id}-fargate-task",
        compatibility=aws_ecs.Compatibility.FARGATE,
        network_mode=aws_ecs.NetworkMode.AWS_VPC,
        cpu="256",
        memory_mib=mem_limit,
    )


def get_fargate_container(scope: core.Construct, construct_id: str, task: aws_ecs.TaskDefinition,
        mem_limit: str, environment: Optional[Mapping] = None) -> aws_ecs.ContainerDefinition:
    container_log_group = aws_logs.LogGroup(
        scope,
        f"{construct_id}-container-log-group",
        log_group_name=f"/aws/ecs/{construct_id}",
        retention=DEFAULT_LOG_RETENTION,
        removal_policy=core.RemovalPolicy.DESTROY,
    )

    return task.add_container(
        f"{construct_id}-task-container",
        image=aws_ecs.ContainerImage.from_asset(  # pylint: disable=no-value-for-parameter
            directory=f"lib/stacks/{construct_id}/docker".replace("-", "_")),
        memory_limit_mib=int(mem_limit),
        working_directory="/tmp",
        logging=aws_ecs.LogDrivers.aws_logs(  # pylint: disable=no-value-for-parameter
            log_group=container_log_group,
            stream_prefix=construct_id,
        ),
        environment=environment,
    )
