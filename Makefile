ifneq (,$(wildcard .env))
include .env
export
endif

PYTHON ?= python3
SERVER_ADDRESS ?= 127.0.0.1:5000
DEMO_SERVER_ADDRESS ?= hexworld.playit.plus:1048
clients ?= 1

.PHONY: build check up clean demo

build:
	$(PYTHON) -m pip install -r client/requirements.txt

check:
	$(PYTHON) -m compileall -q client/src

up:
	set -e; \
	for id in $$(seq 1 $(strip $(clients))); do \
		(cd client && \
			SERVER_ADDRESS=$(SERVER_ADDRESS) \
			CLIENT_ID=$$id \
			SESSION_PATH=data/session_$$id.json \
			$(PYTHON) src/main.py) & \
	done; wait

clean:
	rm -f client/data/session*.json

demo:
	$(MAKE) up SERVER_ADDRESS=$(DEMO_SERVER_ADDRESS)
