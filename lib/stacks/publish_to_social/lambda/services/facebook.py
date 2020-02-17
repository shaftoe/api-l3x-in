import utils
import utils.handlers


def handler(event, context) -> utils.Response:
    """lambda entry point"""
    return utils.handlers.EventHandler(
        name="facebook",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=lambda x: NotImplementedError(
            "Facebook POST /feed API endpoint not available anymore: "
            "https://developers.facebook.com/docs/graph-api/reference/v6.0/user/feed")
    ).response
