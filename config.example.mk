export AWS_PROFILE := <your-profile>

export CDK_STACKS := '*'
export API_DOMAIN := your.domain.com

export CORS_ALLOW_ORIGIN := https://www.domain.com/
export LAMBDA_FUNCTIONS := <comma-separated list of social to enable. e.g: facebook, mastodon, twitter>
export LAMBDA_FUNCTIONS_LOG_LEVEL := DEBUG
export LAMBDA_LAYERS := bs4, requests_oauthlib

# 3rd party tokens
export GITHUB_TOKEN := xxxx
export TWITTER_OAUTH_CONSUMER_KEY := xxxx
export TWITTER_OAUTH_CONSUMER_SECRET := xxxx
# etc ...
