import utils
import utils.handlers


def handler(event, context) -> utils.Response:
    """lambda entry point"""
    return utils.handlers.EventHandler(
        name="facebook",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=lambda x: NotImplementedError(
            "Facebook APIs don't allow post of content to user feed: "
            "https://developers.facebook.com/docs/graph-api/using-graph-api/#publishing")
    ).response
