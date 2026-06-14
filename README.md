# HexWorld

**Universidade Federal de Viçosa — Campus Florestal**

**Instituto de Ciências Exatas e Tecnológicas**

**Bacharelado em Ciência da Computação**

**CCF 355 — Sistemas Distribuídos e Paralelos**

**Professora:** Thais Regina de Moura Braga Silva

**Grupo:** Alan Araújo dos Reis (5096) · Gabriel Rodrigues Marques (5097)

---

Editor colaborativo de mapas hexagonais para jogadores e mestres de RPG. Múltiplos usuários editam o mesmo mapa em tempo real; o servidor propaga cada alteração a todos os clientes conectados.

---

## Server (Docker)

```bash
docker compose up --build # cria o contêiner e inicia o servidor
```

---

## Client (Local)

```bash
make build # cria o ambiente virtual e instala as dependências
make check # verifica sintaxe do client
make up # abre o cliente e conecta ao servidor local
```

**Contas disponíveis:**

| Usuário | Senha       |
|---------|-------------|
| `user1` | `password1` |
| `user2` | `password2` |
| `user3` | `password3` |
| `user4` | `password4` |

**Múltiplos clientes simultâneos:**

```bash
make up clients=4 # abre 4 instâncias do cliente com sessões separadas
make clean # remove sessões locais
```

---

### Servidor Público (Playit.gg)

Para conectar ao servidor público já configurado:

```bash
make demo # abre o cliente e conecta ao servidor público (hexworld.playit.plus:1048)
```

---

## Desenvolvimento

```bash
make check # verificação rápida de sintaxe do client (client + server)
```

---

## Reiniciar Banco de Dados

```bash
docker compose down # desliga o contêiner do servidor
sudo rm -f server/data/hexworld.db  # remove o banco de dados
docker compose up --build # recria o contêiner e inicia o servidor
```

---

## Hospedar Publicamente (opcional)

Para expor o servidor via túnel TCP:

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
