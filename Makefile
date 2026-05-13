PYTHON ?= python3
SERVER_ADDRESS ?= 127.0.0.1:5000
clients ?= 1

.PHONY: build check up clean

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
