import utils
import utils.handlers


def handler(event, context) -> utils.Response:
    """lambda entry point"""
    return utils.handlers.EventHandler(
        name="facebook",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=lambda x: "success",
    ).response
