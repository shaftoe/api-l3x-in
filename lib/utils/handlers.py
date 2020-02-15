from typing import (Callable, Union)
import json
from sys import getsizeof

from . import (
    HandledError,
    Log,
    Response,
    LambdaEvent,
    LambdaContext,
)

MAX_EVENT_SIZE = 10 * 1024  # 10Kbytes

class EventHandler:

    def __init__(self, name: str, event: LambdaEvent, context: LambdaContext, action: Callable[[dict], None]):
        """Generic Lambda event handler

        It takes care of properly handling exceptions and logging.

        Overwrite self.pre_action to add custom logic that will
        be executed before provided `action(self._event)` is triggered

        Return from self._action(self._event) is discarded.

        `response` property returns a JSON-serializable object that implements
        the API Gateway response interface.

        :param name:     name of lambda caller
        :param event:    AWS Lambda runtime event object
        :param context:  AWS Lambda runtime context object, ref https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
        :param action:   callable to be executed (self._event is passed as argument)
        """
        self._name     = name.lower()
        self._event    = event
        self._context  = context
        self._action   = action
        self._response = Response()

        Log.info("Request of execution from Lambda '{}' version {}".format(self._context.function_name,
                                                                           self._context.function_version))

        # Sanitize input
        Log.debug("Ensure event size is not above the limit of {} bytes".format(MAX_EVENT_SIZE))

        if getsizeof(self._event) > MAX_EVENT_SIZE:
            raise HandledError(
                "Event payload exceeds limits: received {} bytes, "
                "max allowed {}".format(getsizeof(self._event), MAX_EVENT_SIZE))

    def pre_action(self):
        """
        Overwrite this method to add custom logic for custom
        input type (Lambda RequestResponse, SNS, API Gateway, etc...)
        """
        Log.debug("Calling EventHandler (empty) pre_action")

    @property
    def response(self) -> Response:
        Log.debug('Handling event: {}'.format(self._event))

        try:
            self.pre_action()

            Log.debug("Calling action '{}' with argument '{}'".format(self._action,
                                                                      self._event))
            self._response.put(self._action(self._event))

        except BaseException as error:
            Log.debug("Catched Exception of class '{}'".format(error.__class__.__name__))

            self._response.put(error)

            # Ensure Lambda gets retriggered only when termination is handled
            if isinstance(error, SystemExit):
                Log.critical("Non-zero return code, Lambda execution will be retried by AWS")
                raise error

        Log.info("Event handling complete")
        Log.debug("Response: {}".format(self._response))

        return self._response


class SnsEventHandler(EventHandler):

    def __init__(self, name: str, event: LambdaEvent, context: LambdaContext, action: Callable[[dict], None], disable: Union[str, None]="disable"):
        """SNS-triggered Lambda event handler

        :param disable: pre_action will check in event[disable] list for lambdas **NOT to be executed**. Set to None if that is not what you want
        """
        super().__init__(name, event, context, action)
        self._disable = disable

    def _parse_event(self) -> None:
        Log.debug("Parsing event in search for SNS data")

        records = self._event["Records"]

        if len(records) != 1:
            raise HandledError("SNS response 'Records' items "
                               "is of length {}, expected 1".format(len(records)),
                               status_code=500)

        message_id = records[0]["Sns"]["MessageId"]
        subject    = records[0]["Sns"]["Subject"]

        Log.info("Found SNS content in event: MessageId '{}', Subject '{}'".format(message_id, subject))

        Log.debug("Deserializing JSON message content")
        self._event = json.loads(records[0]["Sns"]["Message"])
        Log.debug("SNS Message content: '{}'".format(self._event))

        Log.info("Parsing SNS event complete successfully")

    def pre_action(self) -> None:
        Log.info("PreProcessing SNS event")
        self._parse_event()

        if self._disable in self._event:
            Log.debug("Found '{}' key in SNS content".format(self._disable))

            if self._name in self._event[self._disable] or \
                    "all" in self._event[self._disable]:
                Log.debug("{} (or 'all' wildcard) in '{}'".format(self._name, self._disable))

                raise HandledError(
                    message="Execution of lambda '{}' "
                            "disabled by client request".format(self._name),
                    status_code=304,  # HTTP not modified
                )

            else:
                Log.debug("{} not in '{}'".format(self._name, self._disable))


class ApiGatewayEventHandler(EventHandler):

    def __init__(self, name: str, event: LambdaEvent, context: LambdaContext, action: Callable[[dict], None]):
        """ApiGateway-triggered Lambda event handler"""
        super().__init__(name, event, context, action)

    def pre_action(self) -> None:
        try:
            method, path = self._event["httpMethod"], self._event["path"]
            Log.info("Processing HTTP {} request for path {}".format(method, path))

        except KeyError as error:
            raise HandledError("Missing 'httpMethod' or 'path' in event")

        route = "{} {}".format(self._event.get("httpMethod", "").upper(),
                               self._event.get("path", "").lower())

        Log.debug("Adding 'route' key to event object with value '{}'".format(route))
        self._event["route"] = route
