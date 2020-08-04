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

    package_dir={"": "lib"},
    packages=setuptools.find_packages(where="lib"),

    install_requires=[
        "aws-cdk.core",
        "aws-cdk.aws-apigateway",
        "aws-cdk.aws-certificatemanager",
        "aws-cdk.aws-cloudtrail",
        "aws-cdk.aws-dynamodb",
        "aws-cdk.aws-ec2",
        "aws-cdk.aws-ecs",
        "aws-cdk.aws-events",
        "aws-cdk.aws-events-targets",
        "aws-cdk.aws-iam",
        "aws-cdk.aws-lambda",
        "aws-cdk.aws-lambda-destinations",
        "aws-cdk.aws-logs",
        "aws-cdk.aws-s3",
        "aws-cdk.aws-s3-notifications",
        "aws-cdk.aws-sns",
        "aws-cdk.aws-sns-subscriptions",
        "boto3",
        "feedparser",
        "html2text",
        "pylint",
        "pytest",
        "pytest-cov",
        "requests",
    ],

    python_requires=">=3.8",

    # FIXME: add proper metadata
)
