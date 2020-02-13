import setuptools


VERSION = None

with open("VERSION") as f:
    VERSION = f.read().rstrip()

with open("README.md") as f:
    LONG_DESC = f.read()

setuptools.setup(
    name="api-l3x-in",
    version=VERSION,

    description="api.l3x.in source code",
    long_description=LONG_DESC,
    long_description_content_type="text/markdown",

    author="Alexander Fortin",

    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),

    install_requires=[
        "aws-cdk.core",
        "aws-cdk.aws-apigateway",
        "aws-cdk.aws-certificatemanager",
        "aws-cdk.aws-lambda",
        "aws-cdk.aws-logs",
        "aws-cdk.aws-sns",
        "aws-cdk.aws-sns-subscriptions",
        "boto3",
    ],

    python_requires=">=3.8",

    # FIXME: add proper metadata
)
