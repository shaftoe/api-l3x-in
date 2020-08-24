from io import BufferedIOBase
from time import (sleep, time)
from typing import (
    Dict,
    Mapping,
    Iterable,
    List,
    Optional,
    Union,
)
import json

from . import (
    HandledError,
    Log,
    Response,
)

from .helpers import  import_non_stdlib_module

boto3 = import_non_stdlib_module("boto3")
boto_exceptions = import_non_stdlib_module("botocore.exceptions")


def invoke_lambda(name: str, payload: dict, invoke_type: str = "RequestResponse") -> Response:
    """Trigger AWS Lambda execution."""
    if invoke_type not in ("DryRun", "RequestResponse", "Event"):
        raise HandledError(f"invalid invoke_type: {invoke_type}", status_code=400)

    response = Response()

    session = boto3.session.Session()
    client = session.client("lambda")

    Log.debug("Invoking lambda %s", name)

    lambda_resp = client.invoke(
        FunctionName=name,
        InvocationType=invoke_type,
        Payload=json.dumps(payload))

    Log.debug("Lambda %s invocation succesful", name)

    if invoke_type in ("DryRun", "RequestResponse"):
        Log.debug("Deserializing Lambda response Payload")
        lambda_payload = json.load(lambda_resp["Payload"])
        response.put(lambda_payload)

    if not 200 <= lambda_resp["StatusCode"] < 300:
        raise HandledError(message=f"lambda response: {lambda_resp}",
                           status_code=lambda_resp["StatusCode"])

    return response


def publish_to_sns_topic(sns_topic: str, subject: str, content: dict) -> Response:
    """
    :returns: SNS MessageId
    """
    Log.info("Sending message with subject '%s' to SNS topic %s", subject, sns_topic)
    Log.debug("Message: %s", content)

    session = boto3.session.Session()
    client = session.client("sns")

    sns_response = client.publish(
        TopicArn=sns_topic,
        Message=json.dumps(content),
        Subject=subject,
    )

    try:
        response = Response()
        response.put(sns_response["MessageId"])
        return response

    except KeyError:  # Hard exit to ensure Lambda is requeued for retrial
        raise SystemExit("Missing MessageId in SNS response")


def get_all_loggroups():
    """Return list of CloudWatch LogGroups in the account."""
    Log.debug("Retrive all LogGroups names in CloudWatch.")
    session = boto3.session.Session()
    client = session.client("logs")

    response = client.describe_log_groups()
    groups = [lg["logGroupName"] for lg in response["logGroups"]]

    if groups:
        Log.debug("Found LogGroups: %s", ",".join(groups))
    else:
        Log.debug("No LogGroups found")

    return groups


def send_event_to_logstream(log_group: str, log_stream: str, message: Mapping) -> str:
    Log.debug("Send event content to CloudWatch LogGroup %s Stream %s",
              log_group, log_stream)

    session = boto3.session.Session()
    client = session.client("logs")

    sequence_token = None
    done = False
    retrials = 3

    if message:
        Log.debug("message content: %s", message)
    else:
        raise HandledError("No content to send to Log Stream, aborting", status_code=500)

    event = {
        "timestamp": int(time() * 1000),  # milliseconds after Jan 1, 1970 00:00:00 UTC
        "message": json.dumps(message),
    }

    while (not done) and retrials > 0:
        try:
            if sequence_token:
                Log.debug("Found Stream sequence_token %s", sequence_token)
                client.put_log_events(
                    logGroupName=log_group,
                    logStreamName=log_stream,
                    logEvents=[event],
                    sequenceToken=sequence_token,
                )

            else:
                Log.debug("Trying put_log_events without Stream sequence_token")
                client.put_log_events(
                    logGroupName=log_group,
                    logStreamName=log_stream,
                    logEvents=[event],
                )

            done = True
            return "Successfully delivered event content " \
                   "to CloudWatch LogGroup %s Stream %s" % (log_group, log_stream)

        except boto_exceptions.ClientError as error:
            Log.debug("Catched CloudWatch Logs client error code %s",
                      error.response['Error']['Code'])

            if error.response['Error']['Code'] in ["DataAlreadyAcceptedException",
                                                   "InvalidSequenceTokenException"]:
                Log.debug(
                    "Fetching sequence_token from boto error response['Error']['Message'] %s",
                    error.response["Error"]["Message"])
                # NOTE: apparently there's no sequenceToken attribute in the response so we have
                # to parse response["Error"]["Message"] string
                sequence_token = error.response["Error"]["Message"].split(":")[-1].strip(" ")
                Log.debug("Setting sequence_token to %s", sequence_token)

                retrials -= 1

                if retrials > 0:
                    Log.debug("Retrying %d more time(s)...", retrials)

                else:
                    raise HandledError(
                        "Failed sending event content to CloudWatch Logs "
                        "after 3 retrials",
                        status_code=500)

            else:
                raise HandledError("Unexpected response from boto client: %s" % error,
                                   status_code=500)


def read_log_stream(log_group: str, log_stream: str, start_time: Optional[int] = 0) -> Iterable:
    """Return all events from log stream.

    :param start_time: optional UNIX epoch in milliseconds
    """
    Log.debug("Read events from CloudWatch LogGroup %s Stream %s",
              log_group, log_stream)

    session = boto3.session.Session()
    client = session.client("logs")

    resp = client.get_log_events(logGroupName=log_group,
                                 logStreamName=log_stream,
                                 startTime=start_time)

    Log.info("Found %d events", len(resp["events"]))
    Log.debug("Events: %s", resp["events"])

    return resp["events"]


def delete_log_stream(log_group: str, log_stream: str) -> None:
    """Delete log stream."""
    Log.debug("Delete CloudWatch LogGroup %s Stream %s", log_group, log_stream)

    session = boto3.session.Session()
    client = session.client("logs")

    client.delete_log_stream(
        logGroupName=log_group,
        logStreamName=log_stream,
    )


def read_all_log_streams(log_group: str) -> Mapping:
    Log.info("Read all events from all CloudWatch LogGroup %s Streams", log_group)

    session = boto3.session.Session()
    client = session.client("logs")
    resp = client.describe_log_streams(logGroupName=log_group)

    streams = [stream["logStreamName"] for stream in resp["logStreams"]]

    return {stream: read_log_stream(log_group=log_group, log_stream=stream)
            for stream in streams}


def put_object_to_s3_bucket(key: str, bucket: str,
                            body: Union[BufferedIOBase, bytes],
                            wait: Optional[bool] = False) -> Mapping:
    Log.info("Put key %s to S3 bucket %s", key, bucket)

    session = boto3.session.Session()
    client = session.client("s3")

    response = client.put_object(Body=body, Bucket=bucket, Key=key)

    if wait:
        client.get_waiter("object_exists").wait(Bucket=bucket, Key=key)

    return response


def get_object_from_s3_bucket(key: str, bucket: str) -> BufferedIOBase:
    Log.info("Get key %s from S3 bucket %s", key, bucket)

    session = boto3.session.Session()
    client = session.client("s3")

    try:
        response = client.response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"]

    except boto_exceptions.ClientError as error:

        if error.response["Error"]["Code"] == "NoSuchKey":
            raise HandledError("Key %s not found in bucket %s" % (key, bucket), status_code=404)

        raise error


def trigger_ecs_fargate_task(task: str, cluster: str,
                             subnets: List[str], security_groups: List[str],
                             assign_public_ip: Optional[bool] = True,
                             overrides: Optional[Mapping] = None) -> Mapping:
    Log.info("Trigger Fargate task %s", task)

    session = boto3.session.Session()
    client = session.client("ecs")

    if overrides:
        Log.info("Setting overrides to %s", overrides)
    else:
        overrides = {}

    response = client.run_task(
        cluster=cluster,
        taskDefinition=task,
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": security_groups,
                "assignPublicIp": "ENABLED" if assign_public_ip else "DISABLED",
            },
        },
        overrides=overrides,
    )

    Log.debug("Response: %s", response)
    return response


def scan_dynamodb_table(table_name: str):
    """Scan DynamoDB table, return boto3 response.

    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.scan
    """
    Log.info("Scan DynamoDB table %s", table_name)

    session = boto3.session.Session()
    client = session.client("dynamodb")

    response = client.scan(TableName=table_name)

    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        raise HandledError(message="Unexpected DynamoDB return code",
                           status_code=response["ResponseMetadata"]["HTTPStatusCode"])

    Log.debug("Response: %s", response)
    return response


def run_insights_query(log_groups: List[str], query: str, start_time: int, end_time: int) -> str:
    """Run given CloudWatch Logs Insights query for given LogGroups, return query ID."""
    session = boto3.session.Session()
    client = session.client("logs")

    Log.info("Run CloudWatch Logs Insights query for log groups %s", ", ".join(log_groups))
    Log.debug("Query: %s", query)

    response = client.start_query(
        logGroupNames=log_groups,
        startTime=start_time,
        endTime=end_time,
        queryString=query,
    )

    Log.info("Query with id %s running", response["queryId"])
    return response["queryId"]


def get_insights_query_results(query_id: str) -> list:
    """Poll CloudWatch Logs Insights for query results, return results list."""
    delay = 2  # polling frequency in seconds
    session = boto3.session.Session()
    client = session.client("logs")
    response = {}

    Log.info("Inspecting status for query_id %s", query_id)
    while len(response) == 0 or response.get("status") == "Running":
        Log.debug("Sleeping %d seconds for query %s to complete...", delay, query_id)
        sleep(delay)
        response = client.get_query_results(queryId=query_id)

    Log.info("Query %s status: %s", query_id, response["status"])
    Log.debug("Query %s response: %s", query_id, response["results"])
    return response["results"]


def update_dynamo_item(table_name: str, key: dict, att_updates: dict):
    """Run update_item on DynamoDB table."""
    session = boto3.session.Session()
    client = session.client("dynamodb")

    return client.update_item(TableName=table_name, Key=key, AttributeUpdates=att_updates)


def list_bucket(bucket_name: str) -> List[Dict]:
    """Return list of S3 bucket keys."""
    session = boto3.session.Session()
    client = session.client("s3")

    Log.debug("Fetching keys list from bucket %s", bucket_name)
    result = client.list_objects_v2(Bucket=bucket_name)

    try:
        assert "KeyCount" in result
        assert "ResponseMetadata" in result
        assert "HTTPStatusCode" in result["ResponseMetadata"]
        assert result["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert "Contents" in result

    except AssertionError as error:
        raise HandledError(f"Unexpected S3 response: {error}") from error

    Log.debug("Found %d key(s): %s", result["KeyCount"], result["Contents"])
    return result["Contents"]
