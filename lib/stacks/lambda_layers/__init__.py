from os import environ as env
from aws_cdk import (
    aws_lambda,
    core,
)


from utils.cdk import (
    code_from_path,
    DEFAULT_RUNTIME,
)


class LambdaLayersStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        """
        Provide `layers` attribute as shareble mapping of available Lambda Layers.

        e.g.
        self.layers = {
            "requests": requests_layer,
            "bs4:, bs4_layer,
            ...
        }

        XXX: maybe replace `requests` layer with AWS officially supported one:
        https://aws.amazon.com/blogs/compute/upcoming-changes-to-the-python-sdk-in-aws-lambda/
        """

        super().__init__(scope, id, **kwargs)

        def build_layer(name):
            """Builder function for aws_lambda.LayerVersion objects."""
            return aws_lambda.LayerVersion(
                self,
                "lambda-layer-python3-{}".format(name),
                code=code_from_path(path="lib/stacks/{}/layers/{}".format(id, name)),
                compatible_runtimes=[
                    aws_lambda.Runtime.PYTHON_3_7,
                    DEFAULT_RUNTIME,
                ],
                license="Apache-2.0",
                description="Adds {} dependecy".format(name),
            )

        self.layers = {layer.lower(): build_layer(layer)
                       for layer in env.get("LAMBDA_LAYERS", "")
                                       .replace(" ", "")
                                       .split(",")
                                       if layer}
