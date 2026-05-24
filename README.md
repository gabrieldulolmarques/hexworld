# HexWorld

## Server (Docker)

```bash
docker compose up --build # cria o contêiner e inicia o servidor
```

---

## Client (Local)

**Contas disponíveis:**
| Usuário | Senha |
|---------|-------|
| `user1` | `password1` |
| `user2` | `password2` |
| `user3` | `password3` |
| `user4` | `password4` |

---

```bash
make build # cria o ambiente virtual e instala as dependências
make up # conecta em 127.0.0.1:5000 e abre o cliente
```

Múltiplos Clientes:

```bash
make up clients=4 # múltiplos clientes simultâneos
make clean # remove sessões locais

```

---

### Servidor Público (Playit.gg)

Para conectar ao servidor público já configurado no Playit.gg, execute:

```bash
make demo # usa o servidor público hexworld.playit.plus:1048
```

---

## Hospedar Publicamente (opcional)

Para expor o servidor publicamente via túnel TCP:

1. Obtenha a `SECRET_KEY` em [Playit.gg → Docker](https://playit.gg/account/setup/wizard/new-account/docker/docker-name).
2. Copie `.env.example` para `.env` e preencha a chave.
3. No [painel de túneis](https://playit.gg/account/tunnels), crie um túnel **TCP** com endereço local `10.1.0.2:5000`.
4. Defina `DEMO_SERVER_ADDRESS` no `.env` com o endereço público gerado.

---

## Reiniciar Banco de Dados

```bash
docker compose down # destrói o contêiner
sudo rm -f server/data/hexworld.db # remove o banco de dados
docker compose up --build # cria o contêiner e inicia o servidor novamente
```
