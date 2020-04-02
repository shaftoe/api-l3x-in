from datetime import (datetime, timedelta)
from os import environ as env

import utils
import utils.aws as aws
import utils.handlers as handlers


def _send_email(subject: str, content: str) -> utils.Response:
    utils.Log.info("Send report via %s email notification service", env["LAMBDA_NOTIFICATIONS"])

    return aws.invoke_lambda(
        name=env["LAMBDA_NOTIFICATIONS"],
        payload={
            "subject": subject,
            "text": content,
        },
        invoke_type="Event")


def _create_document(own_log_group: str) -> str:
    """Create Markdown report of errored logs in CloudWatch."""
    # We fetch logs from yesterday's at 00:00
    start_time = datetime.utcnow() - timedelta(days=1)
    start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    start_seconds = int(start_time.timestamp() * 1000)

    report = {}

    groups = [group for group in aws.get_all_loggroups()
              if not group == own_log_group]

    for group in groups:
        utils.Log.info("Processing group %s", group)

        streams = aws.read_all_log_streams(log_group=group)

        for stream in streams:
            utils.Log.info("Processing stream %s", stream)
            events = aws.read_log_stream(log_group=group, log_stream=stream, start_time=start_seconds)

            if events:
                report[group] = []
                for event in events:
                    msg = event["message"]
                    if any(map(msg.startswith, ["[ERR", "[WARN"])):
                        report[group].append(msg)
            else:
                utils.Log.info("Deleting empty stream %s", stream)
                aws.delete_log_stream(log_group=group, log_stream=stream)

    # Remove groups with empty content
    report = {group: content for group, content in report.items() if content}

    if report:
        utils.Log.info("Found content, generating Markdown report")
        output = "# CloudWatch Logs ERR/WARN report\n\n"
        for group, content in report.items():
            output += f"## {group}\n\n"
            for line in content:
                output += f"{line}\n"

        return output

    utils.Log.info("Empty report, exiting without output")


def send_report(event: utils.LambdaEvent):
    """Send report as Markdown email attachment."""
    markdown = _create_document(own_log_group=event["own_log_group"])
    if not markdown:
        raise utils.HandledError("Error creating Markdown content")

    today = datetime.utcnow().strftime(format="%Y-%m-%d")

    _send_email(subject=f"AWS CloudWatch Logs report - {today}", content=markdown)

    utils.Log.info("All done")


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    event["own_log_group"] = context.log_group_name

    return handlers.EventHandler(
        name="send_report",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=send_report,
    ).response
