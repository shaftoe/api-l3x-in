"""
Lambda function that queries yesterday's CloudWatch Logs for errors and sends
an email report with Markdown formatted content.
"""
from datetime import (datetime, timedelta)
from os import environ as env
from re import match
from typing import Union
import itertools

import utils
import utils.aws as aws
import utils.handlers as handlers
import utils.helpers as helpers


# Ref: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html
FIELDS = ["@message", "@log", "@logStream"]
QUERY = ' | '.join([
    f'FIELDS {", ".join(FIELDS)}',
    'FILTER @message not like "DEBUG"',
    'FILTER @message like "ERROR"',
])


def _send_email(subject: str, content: str) -> utils.Response:
    utils.Log.info("Send report via %s email notification service", env["LAMBDA_NOTIFICATIONS"])

    return aws.invoke_lambda(
        name=env["LAMBDA_NOTIFICATIONS"],
        payload={
            "subject": subject,
            "text": content,
        },
        invoke_type="Event")


def _get_insight_logs() -> dict:
    """Execute CloudWatch Logs Insight with global QUERY."""
    logs = {}
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    end_time = helpers.midnightify(now)
    start_time = helpers.midnightify(yesterday)
    max_groups = 20

    utils.Log.info("Considering log events between %s and %s", start_time, end_time)

    groups = [group for group in aws.get_all_loggroups() if group.startswith("/aws/")]
    group_chunks = [chunk for chunk in (groups[i:i + max_groups]  # pylint: disable=unnecessary-comprehension
                                        for i in range(0, len(groups), max_groups))]
    if len(group_chunks) > 1:
        utils.Log.info(
            "AWS Logs Insights supports only %d groups per query"
            "Splitting LogGroups in %d chunks", max_groups, len(group_chunks))
        utils.Log.debug(group_chunks)

    def run_query(_groups):
        return aws.get_insights_query_results(
            query_id=aws.run_insights_query(log_groups=_groups,
                                            query=QUERY,
                                            start_time=round(start_time.timestamp()),
                                            end_time=round(end_time.timestamp())))

    futures = helpers.exec_in_thread_and_wait(*((run_query, groups) for groups in group_chunks))
    results = itertools.chain.from_iterable(future.result() for future in futures.done)

    log_entries = [{entry["field"]: entry["value"] for entry in result}
                   for result in results]

    for entry in log_entries:
        # Using regex to remove leading account number from LogGroup name
        group = match(r'\d+:(.*)', entry["@log"]).groups()[0]
        msg, stream = entry["@message"], entry["@logStream"]

        if group not in logs:
            logs[group] = {}

        if stream not in logs[group]:
            logs[group][stream] = []

        logs[group][stream].append(msg)

    return logs


def _create_md_document(logs: dict) -> Union[str, None]:
    """Create Markdown report from logs dictionary.

    `logs` format is:
    {
        groupName: {
            streamName: [message, message, ...],
            streamName: [message, message, ...],
            ...
        },
        groupName: {
            ...
        }
    }
    """
    output = None

    if logs:
        utils.Log.info("Found content, generating Markdown report")
        output = "# CloudWatch Logs ERROR report\n"

        for group in logs:
            output += f"\n## {group}\n"

            for stream in logs[group]:
                output += f"\n### {stream}\n\n"

                for message in logs[group][stream]:
                    output += f"- {message.rstrip()}\n"

    return output


def send_report(_: utils.LambdaEvent):
    """Send report formatted as Markdown via email service."""
    markdown = _create_md_document(logs=_get_insight_logs())

    if markdown:
        today = datetime.utcnow().strftime(format="%Y-%m-%d")
        _send_email(subject=f"AWS CloudWatch Logs report - {today}", content=markdown)

    else:
        utils.Log.info("Empty report, exiting without output")

    utils.Log.info("All done")


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="send_report",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=send_report,
    ).response
