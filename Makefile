.PHONY: venv deps-txt-update dev-venv run build test test-docker
.ONESHELL:

ENV_FILE := $(realpath .env)
ENV_VARS := $(shell set -a && . $(ENV_FILE) && env | grep '=')
$(foreach v,$(ENV_VARS),$(eval export $(v)))

IMAGE ?= pyformatic-demo

venv:
	python${PYTHON_VERSION} -m venv .dev-venv

deps-update: venv
	.dev-venv/bin/pip3 install --upgrade pip
	.dev-venv/bin/pip3 install pip-tools
	.dev-venv/bin/pip-compile -r -v --all-extras --upgrade --emit-find-links \
		--cache-dir .dev-venv/.cache/pip-tools --resolver backtracking --emit-index-url \
		--color requirements.in
	.dev-venv/bin/pip-compile -r -v --all-extras --upgrade --emit-find-links \
		--cache-dir .dev-venv/.cache/pip-tools --resolver backtracking --emit-index-url \
		--color requirements-demo.in
	.dev-venv/bin/pip-compile -r -v --all-extras --upgrade --emit-find-links \
		--cache-dir .dev-venv/.cache/pip-tools --resolver backtracking --emit-index-url \
		--color requirements-dev.in

dev: venv
	.dev-venv/bin/pip3 install --upgrade pip
	.dev-venv/bin/pip3 --cache-dir .dev-venv/.cache/pip-tools install -r requirements-dev.txt
	.dev-venv/bin/playwright install

build:
	docker build -t $(IMAGE) .

run: build
	docker compose up

test-docker: build
	docker compose up -d
	docker compose exec demo pytest -vv
	docker compose down

test: dev
	.dev-venv/bin/uvicorn demo.main:app --host 127.0.0.1 --port 8000 & \
	server_pid=$$!; \
	sleep 2; \
	PYTHONPATH=. DEMO_BASE_URL=http://127.0.0.1:8000 .dev-venv/bin/pytest -v --tb=short --color=yes --cov=pyformatic --cov-report=xml --cov-report=term; \
	kill $$server_pid && sleep 1; \
	echo "Tests completed."

lint: dev
	.dev-venv/bin/pylint --fail-under=9.5 pyformatic tests demo
