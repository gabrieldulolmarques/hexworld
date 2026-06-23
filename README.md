# HexWorld

**Universidade Federal de Viçosa — Campus Florestal**

**Instituto de Ciências Exatas e Tecnológicas**

**Bacharelado em Ciência da Computação**

**CCF 355 — Sistemas Distribuídos e Paralelos**

**Professora:** Thais Regina de Moura Braga Silva

**Grupo:** Alan Araújo dos Reis (5096) · Gabriel Rodrigues Marques (5097)

---

Editor colaborativo de mapas hexagonais para jogadores e mestres de RPG. Múltiplos usuários editam o mesmo mapa em tempo real; o servidor propaga cada alteração a todos os clientes conectados.

Transporte desta branch: **`Sockets`** — TCP + JSON. (A implementação por **RMI** com Pyro5 vive na branch `rmi`.)

---

### Usuários

| Usuário | Senha       |
|---------|-------------|
| `user1` | `password1` |
| `user2` | `password2` |
| `user3` | `password3` |
| `user4` | `password4` |

---


### Servidor

```bash
docker compose up --build              # apenas o servidor de sockets
docker compose --profile public up --build  # + túnel público Playit.gg
docker compose down
```

---

### Cliente

```bash
make build
make up
make up clients=N
make clean
make demo # to-do
```

---

### Verificação de Compilação

```bash
make check
```

---

### Reiniciar Banco de Dados

```bash
docker compose down
sudo rm -f server/data/hexworld.db server/data/hexworld.db-*
docker compose up --build
```

---

### Hospedar publicamente via Playit.gg (opcional)

1. Obtenha a `SECRET_KEY` em [Playit.gg → Docker](https://playit.gg/account/setup/wizard/new-account/docker/docker-name).
2. Copie `.env.example` para `.env` e preencha a chave.
3. No [painel de túneis](https://playit.gg/account/tunnels), crie um túnel **TCP** com endereço local `10.1.0.2:5000`.
4. Defina `DEMO_SERVER_ADDRESS` no `.env` com o endereço público gerado.

---

### Licenças

| Componente | Licença |
|---|---|
| Código-fonte | [GNU GPL v3](LICENSE) |
| Tiles do mapa (`client/assets/map/`) | [CC BY-SA 4.0](client/assets/map/LICENSE) |
| Ícones SVG (`client/assets/icons/`) | [Lucide Icons — ISC](https://lucide.dev/license) |

### Créditos

Os tiles do mapa foram criados por **cmartins** e estão disponíveis em [cmartins.itch.io](https://cmartins.itch.io/).
