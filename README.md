# HexWorld

**Universidade Federal de Viçosa — Campus Florestal**

**Instituto de Ciências Exatas e Tecnológicas**

**Bacharelado em Ciência da Computação**

**CCF 355 — Sistemas Distribuídos e Paralelos**

**Professora:** Thais Regina de Moura Braga Silva

**Grupo:** Alan Araújo dos Reis (5096) · Gabriel Rodrigues Marques (5097)

---

Editor colaborativo de mapas hexagonais para jogadores e mestres de RPG. Múltiplos usuários editam o mesmo mapa em tempo real; o servidor propaga cada alteração a todos os clientes conectados.

Transporte desta branch: **`Remote Method Invocation (RMI)`** — Pyro5 + Name Server. (A implementação por **Sockets** TCP+JSON vive na branch `sockets`.)

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
docker compose up --build     # Name Server (Pyro5) + servidor RMI
docker compose down
```

---

### Cliente

```bash
make build
make up
make up clients=N
make clean
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

### Licenças

| Componente | Licença |
|---|---|
| Código-fonte | [GNU GPL v3](LICENSE) |
| Tiles do mapa (`client/assets/map/`) | [CC BY-SA 4.0](client/assets/map/LICENSE) |
| Ícones SVG (`client/assets/icons/`) | [Lucide Icons — ISC](https://lucide.dev/license) |

### Créditos

Os tiles do mapa foram criados por **cmartins** e estão disponíveis em [cmartins.itch.io](https://cmartins.itch.io/).
