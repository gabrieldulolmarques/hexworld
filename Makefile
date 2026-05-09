PYTHON ?= python3
SERVER_HOST ?= 127.0.0.1
SERVER_PORT ?= 5000
CLIENT_ID ?= 1
scale ?= 1

.PHONY: build check up clean

build:
	$(PYTHON) -m pip install -r client/requirements.txt

check:
	$(PYTHON) -m compileall -q client/src

up:
	@if [ "$(scale)" = "1" ]; then \
		cd client && \
		SERVER_HOST=$(SERVER_HOST) \
		SERVER_PORT=$(SERVER_PORT) \
		CLIENT_ID=$(CLIENT_ID) \
		$(PYTHON) src/main.py; \
	else \
		set -e; \
		for id in $$(seq 1 $(scale)); do \
			(cd client && \
				SERVER_HOST=$(SERVER_HOST) \
				SERVER_PORT=$(SERVER_PORT) \
				CLIENT_ID=$$id \
				$(PYTHON) src/main.py) & \
		done; \
		wait; \
	fi

clean:
	rm -f client/data/session*.json
