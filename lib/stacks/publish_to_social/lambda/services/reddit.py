import utils
import utils.handlers


def handler(event, context) -> utils.Response:
    """lambda entry point"""
    return utils.handlers.EventHandler(
        name="reddit",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=lambda x: NotImplementedError("coming soon...")
    ).response
