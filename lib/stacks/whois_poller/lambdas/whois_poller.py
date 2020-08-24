"""Lambda to check if a domain is expiring, thanks to whoisxmlapi.com."""
from datetime import datetime, timedelta
from os import environ as env
from typing import List, Tuple
import json

import utils
import utils.aws as aws
import utils.helpers as helpers
import utils.handlers as handlers

WHOISXMLAPI_ENDPOINT = "https://www.whoisxmlapi.com/whoisserver/WhoisService"
DEFAULT_EXPIRY_DAYS = 14


def _domain_is_expiring(domain: str, days: int = DEFAULT_EXPIRY_DAYS) -> Tuple[str, bool, str]:
    now = datetime.utcnow()
    delta = timedelta(days=days)

    api_key = env["WHOISXMLAPI_KEY"]
    url = f"{WHOISXMLAPI_ENDPOINT}?apiKey={api_key}&domainName={domain}&outputFormat=JSON"

    response = helpers.send_http_request(
        url=url,
        method="GET",
    )
    response = json.loads(response.body)
    expires_date_str = response["message"]["WhoisRecord"]["registryData"]["expiresDate"]
    expires_date = datetime.fromisoformat(expires_date_str.rstrip("Z"))

    return domain, (expires_date - now) < delta, expires_date_str


def alert_if_domain_expired(_: utils.LambdaEvent) -> List[dict]:
    """Check WHOIS data for each domain in WHOIS_DOMAINS env variable, send alert if errors."""
    domains = env["WHOIS_DOMAINS"].replace(" ", "").split(",")

    futures = helpers.exec_in_thread_and_wait((_domain_is_expiring, (domain, ))
                                              for domain in domains)
    results = [future.result() for future in futures.done]

    output = [{
        "domain": result[0],
        "expiringSoon": result[1],
        "expiresDateUTC": result[2],
    } for result in results]

    if any(item["expiringSoon"] for item in output):
        title = "Domain(s) expiring soon"
        msg = ", ".join(f"{item['domain']}={item['expiresDateUTC']}"
                        for item in output if item["expiringSoon"])

        utils.Log.warning("%s: %s", title, msg)
        utils.Log.info("Sending alert notification via %s", env["LAMBDA_NOTIFICATIONS"])

        aws.invoke_lambda(name=env["LAMBDA_NOTIFICATIONS"],
                          payload={
                              "title": title,
                              "payload": msg,
                          })

    return output


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="whois_poller",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=alert_if_domain_expired,
    ).response
