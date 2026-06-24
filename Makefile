ifneq (,$(wildcard .env))
include .env
export
endif

VENV ?= .venv
PYTHON3 ?= python3
VENV_DIR := $(abspath $(VENV))

ifneq ($(wildcard $(VENV)/bin/activate),)
export VIRTUAL_ENV := $(VENV_DIR)
export PATH := $(VENV_DIR)/bin:$(PATH)
endif

SERVER_ADDRESS ?= 127.0.0.1:5000
DEMO_SERVER_ADDRESS ?= hexworld.playit.plus:1048
clients ?= 1
APP_NAME ?= HexWorld

.PHONY: build check up clean demo package

$(VENV)/bin/python:
	@test -d $(VENV) || $(PYTHON3) -m venv $(VENV)
	@$(VENV)/bin/python -m pip install --upgrade pip
	@$(VENV)/bin/python -m pip install -r client/requirements.txt

build: $(VENV)/bin/python

check: $(VENV)/bin/python
	. "$(VENV_DIR)/bin/activate" && PYTHONPYCACHEPREFIX=$(VENV_DIR)/pycache python -m compileall -q client/src server/src

up: $(VENV)/bin/python
	set -e; \
	. "$(VENV_DIR)/bin/activate"; \
	for id in $$(seq 1 $(strip $(clients))); do \
		(cd client && \
			SERVER_ADDRESS=$(SERVER_ADDRESS) \
			CLIENT_ID=$$id \
			SESSION_PATH=data/session_$$id.json \
			python src/main.py) & \
	done; wait

clean:
	rm -f client/data/session*.json

demo: $(VENV)/bin/python
	$(MAKE) up SERVER_ADDRESS=$(DEMO_SERVER_ADDRESS)

package: $(VENV)/bin/python
	$(VENV)/bin/python -m pip install -r client/requirements.txt
	cd client && "$(VENV_DIR)/bin/pyinstaller" --noconfirm --clean --onefile --windowed \
		--name $(APP_NAME) \
		--paths src \
		--add-data "assets:assets" \
		--add-data "src/styles/qss:qss" \
		src/main.py
	@echo "Built client/dist/$(APP_NAME)"
