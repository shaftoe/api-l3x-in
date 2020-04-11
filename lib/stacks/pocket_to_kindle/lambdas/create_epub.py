"""Lambda pocket-to-kindle create_epub."""
from datetime import datetime
from os import environ as env
from os import stat
from subprocess import (run, CalledProcessError, TimeoutExpired)
from tempfile import NamedTemporaryFile
from uuid import uuid4
import shlex

import utils
import utils.aws as aws
import utils.handlers as handlers
import utils.helpers as helpers


def create_epub(event: utils.LambdaEvent) -> str:
    """Build EPUB file from URL source and store it to S3."""
    utils.Log.info("Fetch content from %s", event["url"])
    requests = helpers.import_non_stdlib_module("requests")
    response = requests.get(url=event["url"])

    utils.Log.info("Create Markdown text from %s source", event["url"])
    html2text = helpers.import_non_stdlib_module("html2text")
    markdown_maker = html2text.HTML2Text()
    markdown_maker.ignore_links = True
    markdown = markdown_maker.handle(response.text)
    utils.Log.debug("Markdown content:\n%s", markdown)

    utils.Log.info("Create temporary file to store epub content")
    epub = NamedTemporaryFile(suffix=".epub")
    utils.Log.debug("tempfile created: %s", epub.name)

    # Commands
    pandoc = shlex.split("pandoc --from=markdown --to=epub "
                         f"--metadata=title:'{event['title']}' --output={epub.name}")

    try:
        timeout = 200
        utils.Log.info("Executing %s", shlex.join(pandoc))
        run(pandoc, input=bytes(markdown, encoding="utf-8"), check=True, timeout=timeout)
        utils.Log.info("EPUB creation completed (%d bytes)", stat(epub.name).st_size)

    except TimeoutExpired:
        raise utils.HandledError("Error: pandoc execution exceeded timeout of %d seconds" % timeout,
                                 status_code=500)

    except CalledProcessError as error:
        raise utils.HandledError("Error: %s" % error, status_code=500)

    now = datetime.utcnow()
    file_name = f"pocket-{event['item_id']}" if "item_id" in event else uuid4()
    key_name = now.strftime(f"%Y/%m/%d/{file_name}.epub")

    aws.put_object_to_s3_bucket(key=key_name, bucket=env["EPUB_BUCKET"], body=epub)

    file_url = f"s3://{env['EPUB_BUCKET']}/{key_name}"

    utils.Log.info("File %s created successfully", file_url)

    return f"success: {file_url}"


def handler(event, context) -> utils.Response:
    """Lambda entry point."""
    return handlers.EventHandler(
        name="pocket_create_epub",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=create_epub,
    ).response
