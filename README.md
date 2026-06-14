# HexWorld

**Universidade Federal de Viçosa — Campus Florestal**

**Instituto de Ciências Exatas e Tecnológicas**

**Bacharelado em Ciência da Computação**

**CCF 355 — Sistemas Distribuídos e Paralelos**

**Professora:** Thais Regina de Moura Braga Silva

**Grupo:** Alan Araújo dos Reis (5096) · Gabriel Rodrigues Marques (5097)

---

Editor colaborativo de mapas hexagonais para jogadores e mestres de RPG. Múltiplos usuários editam o mesmo mapa em tempo real; o servidor propaga cada alteração a todos os clientes conectados.

Dois backends de transporte disponíveis no mesmo repositório, escolhidos pela variável `HEXWORLD_TRANSPORT`. Ambos usam o mesmo banco SQLite (`server/data/hexworld.db`).

| Backend | Tecnologia | Como executar |
|---|---|---|
| `sockets` | TCP + JSON framing | `docker compose --profile sockets up` + `make up-sockets` |
| `rmi` | Pyro5 + Name Server | `docker compose --profile rmi up` + `make up-rmi` |

---

## Contas disponíveis

| Usuário | Senha       |
|---------|-------------|
| `user1` | `password1` |
| `user2` | `password2` |
| `user3` | `password3` |
| `user4` | `password4` |

---

## Modo Sockets (Parte 3)

### Servidor

```bash
docker compose --profile sockets up --build   # sobe o servidor na porta 5000
docker compose down                           # derruba
```

### Cliente

```bash
make build               # cria .venv e instala dependências
make up-sockets          # abre 1 cliente conectado a 127.0.0.1:5000
make up-sockets clients=4   # abre 4 instâncias com sessões separadas
make clean               # remove sessões locais
make demo                # conecta ao servidor público (hexworld.playit.plus:1048)
```

---

## Modo RMI — Pyro5 + Name Server (Parte 4)

O backend (Name Server + servidor RMI) sobe via Docker; os clientes (GUI) rodam
no host pelo Make:

```bash
docker compose --profile rmi up --build   # Name Server + servidor RMI
make up-rmi clients=2                       # cliente(s) no host
```

Parar o backend: `docker compose --profile rmi down`.

Os contêineres RMI usam `network_mode: host` (Linux/WSL2): o contêiner compartilha
a rede do host, então os callbacks Pyro5 servidor→cliente funcionam em `127.0.0.1`
sem NAT — sem portas fixas nem configuração extra.

### Variáveis de ambiente relevantes

| Variável | Padrão | Descrição |
|---|---|---|
| `HEXWORLD_TRANSPORT` | `sockets` | Backend de transporte (`sockets` ou `rmi`) |
| `PYRO_NS_HOST` | `127.0.0.1` | Host do Name Server Pyro5 |
| `PYRO_NS_PORT` | `9090` | Porta do Name Server Pyro5 |
| `DATABASE_PATH` | `server/data/hexworld.db` | SQLite compartilhado por sockets e RMI |
| `SERVER_ADDRESS` | `127.0.0.1:5000` | Endereço do servidor (modo sockets) |

---

## Verificação de sintaxe

```bash
make check   # compileall em client/src + server/src
```

---

## Reiniciar banco de dados

```bash
docker compose down
sudo rm -f server/data/hexworld.db server/data/hexworld.db-*
docker compose --profile sockets up --build   # ou --profile rmi
```

Os contêineres do servidor rodam com `user: ${UID}:${GID}` (lidos do `.env`, padrão `1000:1000`), então o SQLite criado em `server/data/` no volume montado fica com o dono do host — sem arquivos `root:root` travando o `rm`.

---

## Hospedar publicamente via Playit.gg (opcional)

1. Obtenha a `SECRET_KEY` em [Playit.gg → Docker](https://playit.gg/account/setup/wizard/new-account/docker/docker-name).
2. Copie `.env.example` para `.env` e preencha a chave.
3. No [painel de túneis](https://playit.gg/account/tunnels), crie um túnel **TCP** com endereço local `10.1.0.2:5000`.
4. Defina `DEMO_SERVER_ADDRESS` no `.env` com o endereço público gerado.

---

## Licenças

| Componente | Licença |
|---|---|
| Código-fonte | [GNU GPL v3](LICENSE) |
| Tiles do mapa (`client/assets/map/`) | [CC BY-SA 4.0](client/assets/map/LICENSE) |
| Ícones SVG (`client/assets/icons/`) | [Lucide Icons — ISC](https://lucide.dev/license) |

### Créditos

Os tiles do mapa foram criados por **cmartins** e estão disponíveis em [cmartins.itch.io](https://cmartins.itch.io/).
