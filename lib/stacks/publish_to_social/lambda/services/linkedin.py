# pylint: disable=line-too-long
import utils
import utils.handlers


def handler(event, context) -> utils.Response:
    """lambda entry point"""
    return utils.handlers.EventHandler(
        name="linkedin",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=lambda x: NotImplementedError(
            "LinkedIn Oauth client credentials (2-legged) flow not available anymore: "
            "https://docs.microsoft.com/en-us/linkedin/shared/authentication/client-credentials-flow")
    ).response
