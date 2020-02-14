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

install_venv: # in the unfortunate case your workstation is still running Python v2
	@$(CHECK_PY) else python3 -m venv .env; fi

check_python:
	@$(CHECK_PY) else \
		printf '$(RED)error: Python v3 required\n'; \
		printf 'install it in the PATH then run:  $(GREEN)`make install_venv`$(CLR)\n'; \
		exit 1; fi

requirements: check_python
	@printf '$(GREEN)$(BOLD)### Install requirements$(CLR)\n'
	pip install --quiet -e .

bootstrap: requirements
	@printf '$(GREEN)$(BOLD)### Bootstrap$(CLR)\n'
	@$(CDK) bootstrap

reminder:
	@printf '$(GREEN)###########################################################################\n'
	@printf '$(GREEN)# remember to add the DNS record to enable owned domain:\n#\n'
	@printf '$(GREEN)# $(YELLOW)$(API_DOMAIN)	$(GREEN)CNAME	$(YELLOW)'
	@aws apigateway get-domain-name \
		--profile $(AWS_PROFILE) \
		--domain-name $(API_DOMAIN) \
		|	grep regionalDomainName \
		| cut -d ':' -f 2 \
		| tr -d ',' \
		| tr -d '"'
	@printf '$(GREEN)###########################################################################$(CLR)\n'

synth: requirements clean
	@printf '$(GREEN)### Synthesizing stacks $(BOLD)$(CDK_STACKS)$(CLR)\n'
	@$(CDK) synth $(CDK_STACKS)

deploy: requirements clean
	@printf '$(GREEN)### Deploying stacks $(BOLD)$(CDK_STACKS)$(CLR)\n'
	@$(CDK) deploy --require-approval never $(CDK_STACKS)

destroy: requirements clean
	@printf '$(RED)### Destroying stacks $(BOLD)$(CDK_STACKS)$(CLR)\n'
	@$(CDK) destroy $(CDK_STACKS)
	@printf '$(GREEN)### Remember to remove leftovers in CloudFormation$(CLR)\n'

list: requirements clean
	@printf '$(GREEN)### Listing available stacks$(CLR)\n'
	@$(CDK) ls

diff: requirements clean
	@printf '$(GREEN)### Diff stacks $(BOLD)$(CDK_STACKS)$(CLR)\n'
	@$(CDK) diff $(CDK_STACKS)

clean:
	@printf '$(GREEN)$(BOLD)### Cleanup local Python caches$(CLR)\n'
	python bin/cleanup_cache.py src/

run-tests:
	@printf '$(RED)FIXME: no test runner available$(CLR)\n'

all: bootstrap deploy reminder

local-run:
	python bin/run.py

create-stack-scaffold:
	# TODO
