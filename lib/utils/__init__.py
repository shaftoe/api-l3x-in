"""
api-l3x-in utilities library

FIXME: Move this package into a dedicated Lambda Layer when this bug is fixed:
       https://github.com/aws/aws-cdk/issues/1972
"""
from os import environ
from typing import (Union, NewType)

import json
import logging
import urllib.parse
import urllib.request


LOG_LEVEL = environ.get("LAMBDA_FUNCTIONS_LOG_LEVEL", "INFO")
Log = logging.getLogger()
Log.setLevel(LOG_LEVEL)

__version__ = None

try:
    __version__ = environ["VERSION"]
    Log.info("api-l3x-in utils v%s, "
             "setting LOG_LEVEL to %s", __version__, LOG_LEVEL)

except KeyError:
    Log.info("api-l3x-in utils, setting LOG_LEVEL to %s", LOG_LEVEL)
    Log.warning("api-l3x-in utils: missing __version__ in environment")

# Using custom types to help reasoning about Lambda metadata
LambdaEvent = NewType("LambdaEvent", dict)
LambdaContext = NewType("LambdaContext", object)


class HandledError(Exception):

    def __init__(self, message: str, status_code: int = 400):
        """
        :param status_code: defaults to HTTP Bad request (400)
        """
        super(HandledError, self).__init__(message)
        self.status_code = status_code


class Response(dict):
    """Response class that implements API Gateway interface.

    Docs:
    https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html

    Subclass `dict` to be JSON serializable: https://stackoverflow.com/a/31207881/2274124
    """

    def __init__(self):
        dict.__init__(self)
        self._text = None
        self._error = None
        self.update({
            "isBase64Encoded": False,
            "headers": {"Access-Control-Allow-Origin": environ.get("CORS_ALLOW_ORIGIN", "*")},
            "body": "{}",
        })

    @property
    def text(self) -> Union[str, None]:
        return self._text

    @property
    def status_code(self) -> int:
        if not self._error:
            return 200

        elif hasattr(self._error, "status_code"):
            return self._error.status_code

        elif isinstance(self._error, NotImplementedError):
            return 501

        else:
            return 500

    def _print_log(self) -> None:
        if 300 <= self.status_code < 500 or self.status_code == 501:
            Log.warning(self._error)

        elif self.status_code == 500 or self.status_code > 501:
            Log.error(self._error)

    def put(self, content: Union[str, Exception]) -> None:
        if isinstance(content, Exception):
            self._error = content
            self._print_log()

        else:
            self._text = content

        self.update({
            "statusCode": self.status_code,
            "body": json.dumps({"error": str(self._error)}
                               if self._error
                               else {"message": self._text},
                               indent=4),
        })
