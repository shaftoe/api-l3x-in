import utils
import utils.handlers


def handler(event, context) -> utils.Response:
    """lambda entry point"""
    return utils.handlers.EventHandler(
        name="hackernews",
        event=utils.LambdaEvent(event),
        context=utils.LambdaContext(context),
        action=lambda x: NotImplementedError("Hackernews APIs don't allow post of content: https://blog.ycombinator.com/hacker-news-api/")
    ).response
