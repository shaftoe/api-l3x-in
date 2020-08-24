'''Get page speed information thanks to Google Pagespeed APIs, store in DynamoDB table.'''
from os import environ as env
from datetime import datetime
from typing import Dict

import utils
import utils.aws as aws
import utils.handlers as handlers
import utils.helpers as helpers


feedparser = helpers.import_non_stdlib_module("feedparser")  # pylint: disable=invalid-name


def _get_last_update(feed_url: str) -> datetime:
    '''Fetch RSS entries, return update datetime for last entry.'''
    utils.Log.info("Fetching content from %s", feed_url)
    last_update = feedparser.parse(feed_url)['entries'][0]['updated_parsed']

    utils.Log.debug('%s updated_parsed: %s', feed_url, last_update)
    return helpers.struct_to_datetime(last_update)


def _get_stored_timestamp() -> Dict[str, str]:
    '''Scan DynamoDB table, return dict of `url: timestamp` items.'''
    data = aws.scan_dynamodb_table(table_name=env['DYNAMODB_TABLE'])

    if data["Count"] == 0:
        utils.Log.warning("Table %s is empty", env['DYNAMODB_TABLE'])
        return []

    items = {item['url']['S']: item['latest_update_timestamp']['S']
             for item in data['Items']}
    utils.Log.debug("Found items: %s", items)
    return items


def deploy_if_feed_updates(_: utils.LambdaEvent):
    '''Trigger deploy if there are updates in the feeds.'''
    netlify_url = f'https://api.netlify.com/build_hooks/{env["NETLIFY_HOOK"]}'
    table_name = env['DYNAMODB_TABLE']
    urls = env['DEPLOYER_FEED_URLS'].replace(' ', '').split(',')

    utils.Log.info("Checking updates for feeds %s", urls)

    stored_timestamps = _get_stored_timestamp()

    def update_feed(feed_url: str) -> bool:
        '''Check if last feed entry is up to date, return True if updated.'''
        last_update = _get_last_update(feed_url)

        # Table might be empty, we treat that case as a miss
        if feed_url in stored_timestamps:
            stored_update = datetime.fromisoformat(stored_timestamps[feed_url])

            utils.Log.debug("%s: checking equality between stored(%s) and last(%s)",
                            feed_url, stored_update, last_update)
            if stored_update == last_update:
                utils.Log.info('%s: no database update needed', feed_url)
                return False

        aws.update_dynamo_item(
            table_name=table_name,
            key={"url": {"S": feed_url}},
            att_updates={
                'latest_update_timestamp': {
                    'Value': {'S': last_update.isoformat()},
                    'Action': 'PUT',
                }
            })

        return True

    futures = helpers.exec_in_thread_and_wait((update_feed, (url, )) for url in urls)

    if any(future.result() for future in futures.done):
        utils.Log.info("Found updates, triggering Netlify deploy")
        helpers.send_http_request(url=netlify_url, method="POST", data={})

    utils.Log.info("All done")


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="deployer",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=deploy_if_feed_updates,
    ).response
