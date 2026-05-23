# HexWorld

## Server (Docker)

Requires a `.env` with `SECRET_KEY` from [playit Docker setup](https://playit.gg/account/setup/wizard/new-account/docker/docker-name). Copy `.env.example` to `.env`.

In the [playit tunnel dashboard](https://playit.gg/account/tunnels), use a **TCP** tunnel with local address `10.1.0.2` and port `5000` (Docker static IP of the `server` service).

```bash
docker compose up --build
```

## Client (Local)

```bash
make build
```
```bash
make up         
```
Demo via playit (set `DEMO_SERVER_ADDRESS` in `.env`, default `hexworld.playit.plus:1048`):

```bash
make demo
```
```bash
make up clients=4
```
```bash
make clean
```
