include defaults.mk
include config.mk

DIR := app
VENV := . .env/bin/activate
CDK := cdk --profile $(AWS_PROFILE)
CHECK_PY := if [ $(shell python --version 2>&1 | cut -c 8) -eq "3" ]; then true;

# Colors: https://stackoverflow.com/a/20983251/2274124
BOLD := $(shell tput bold)
CLR := $(shell tput sgr0)
RED := $(shell tput setaf 1)
GREEN := $(shell tput setaf 2)
YELLOW := $(shell tput setaf 3)
BLUE := $(shell tput setaf 4)

install-venv: # in the unfortunate case your workstation is still running Python v2
	@$(CHECK_PY) else python3 -m venv .env; fi

check-python:
	@$(CHECK_PY) else \
		printf '$(RED)error: Python v3 required\n'; \
		printf 'install it in the PATH then run:  $(GREEN)`make install-venv`$(CLR)\n'; \
		exit 1; fi

requirements: check-python upgrade-pip
	@printf '$(GREEN)$(BOLD)### Install requirements$(CLR)\n'
	pip install --quiet --upgrade pip
	pip install --quiet -e .

cdk-version:
	@printf '$(GREEN)$(BOLD)### Running CDK version $(shell cdk --version) Node.js $(shell node --version)$(CLR)\n'

bootstrap: requirements run-tests cdk-version
	@printf '$(GREEN)$(BOLD)### Bootstrap$(CLR)\n'
	@$(CDK) bootstrap

reminder:
	@printf '$(GREEN)###########################################################################\n'
	@printf '$(GREEN)remember to add $(YELLOW)$(API_DOMAIN)$(GREEN) CNAME DNS record to enable owned domain:\n'
	@printf '$(YELLOW)'
	@aws apigateway get-domain-name \
		--profile $(AWS_PROFILE) \
		--domain-name $(API_DOMAIN) \
		--query "regionalDomainName" \
		--output text
	@printf '$(GREEN)###########################################################################$(CLR)\n'

synth: requirements run-tests clean cdk-version
	@printf '$(GREEN)### Synthesizing stacks $(BOLD)$(CDK_STACKS)$(CLR)\n'
	@$(CDK) synth $(CDK_STACKS)

deploy: requirements run-tests clean cdk-version
	@printf '$(GREEN)### Deploying stacks $(BOLD)$(CDK_STACKS)$(CLR)\n'
	@$(CDK) deploy --require-approval never $(CDK_STACKS)

destroy: requirements run-tests clean cdk-version
	@printf '$(RED)### Destroying stacks $(BOLD)$(CDK_STACKS)$(CLR)\n'
	@$(CDK) destroy $(CDK_STACKS)
	@printf '$(GREEN)### Remember to remove leftovers in CloudFormation$(CLR)\n'

list: requirements run-tests clean cdk-version
	@printf '$(GREEN)### Listing available stacks$(CLR)\n'
	@$(CDK) ls

diff: clean cdk-version
	@printf '$(GREEN)### Diff stacks $(BOLD)$(CDK_STACKS)$(CLR)\n'
	@$(CDK) diff $(CDK_STACKS)

clean:
	@printf '$(GREEN)$(BOLD)### Cleanup local Python caches$(CLR)\n'
	python bin/cleanup_cache.py lib/

pylint:
	@printf '$(GREEN)### Run pylint$(CLR)\n'
	@pylint --errors-only --ignore=layers lib/ test/*py bin/*py setup.py

pytest:
	@printf '$(GREEN)### Run pytest$(CLR)\n'
	@pytest --cov=lib/ test/

run-tests: pylint pytest

upgrade-pip:
	@pip install --quiet --upgrade pip

upgrade-cdk: check-python upgrade-pip
	@pip list --outdated --format=freeze \
		| grep aws-cdk \
		| cut -d = -f 1  \
		| xargs -n1 pip install -U

all: bootstrap deploy reminder

local-run:
	ipython -i bin/run.py

create-stack-scaffold:
	# TODO

# ref: https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-output.html#cli-usage-output-filter
show-loggroups:
	@aws --profile $(AWS_PROFILE) \
		logs describe-log-groups \
		--no-paginate \
		--query 'logGroups[*].{NAME:logGroupName}' \
		--output text

.PHONY: clean diff reminder trigger-lambda find-lambda requirements upgrade-pip upgrade-cdk bootstrap create-stack-scaffold install-venv pytest pylint run-tests cdk-version deploy list show-loggroups check-python destroy local-run synth
