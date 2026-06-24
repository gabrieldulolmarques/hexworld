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

PYRO_NS_HOST ?= 127.0.0.1
PYRO_NS_PORT ?= 9090
clients ?= 1
APP_NAME ?= HexWorld

.PHONY: build check up clean package

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
			PYRO_NS_HOST=$(PYRO_NS_HOST) \
			PYRO_NS_PORT=$(PYRO_NS_PORT) \
			CLIENT_ID=$$id \
			SESSION_PATH=data/session_$$id.json \
			python src/main.py) & \
	done; \
	wait

clean:
	rm -f client/data/session*.json

package: build
	cd client && "$(VENV_DIR)/bin/pyinstaller" --noconfirm --clean --onefile --windowed \
		--name $(APP_NAME) \
		--paths src \
		--add-data "assets:assets" \
		--add-data "src/styles/qss:qss" \
		--collect-submodules Pyro5 \
		--hidden-import serpent \
		src/main.py
	@echo "Built client/dist/$(APP_NAME)"
