# stalse_teste — Documentação

Resumo
Projeto de exemplo que expõe uma API Flask para tickets, integra dados CSV ao SQLite, recalcula métricas via ETL e integra com um workflow n8n.

Índice
- Requisitos
- Execução
- Rotas da API
- Workflow n8n (import & teste)
- Visualização do workflow (screenshot)
- ETL (data/etl.py)
- Trigger (trigger.sh)
- Comandos úteis
- Arquivos-chave
- Observações rápidas

## Requisitos
- Python 3.11 (ou compatível)
- Docker & docker-compose (opcional, recomendado)

## Execução

### Clonar o repositório
Clone o repositório localmente antes de continuar (substitua <repo-url> pelo URL real do seu repositório):

```bash
git clone https://github.com/jonathanbrito48/teste_stalse.git

cd teste_stalse
```

### 1) Sem Docker (desenvolvimento)
1. Criar virtualenv e ativar:
```bash
python3 -m venv venv
source venv/bin/activate
```
2. Instalar dependências:
```bash
pip install -r backend/requirements.txt
```
3. Iniciar API:
```bash
python3 backend/main.py
```

### 2) Com Docker / docker-compose (recomendado)
```bash
docker-compose up --build
```
Serviços principais:
- api (Flask)
- n8n (n8n)
- trigger (executa trigger.sh)

## Rotas da API (arquivo: backend/main.py)

- GET /tickets
  - Função: list_tickets
  - Retorna todos os registros da tabela `tickets` (JSON).

- GET /metrics
  - Função: get_metrics
  - Retorna `data/processed/metrics.json` (gerado pelo ETL).

- PATCH /tickets/<int:ticket>
  - Função: update_status_ticket
  - Body esperado: `{ "status": "Open" }`
  - Validações: `Open`, `In Progress`, `Closed`, `Resolved`.
  - Atualiza `status` no DB.
  - Se o status passar para "Closed", a API deve POSTar para o webhook n8n (ver nota sobre case abaixo).

- PATCH /update_datetime_ticket/<int:ticket>
  - Função: update_time_ticket
  - Body: `{ "close_time": "true" }`
  - Se `close_time == "true"`, define `close_time` do ticket como `now - 3 horas` e atualiza o DB.

- POST /new_tickets
  - Função: create_ticket
  - Recebe lista de tickets (JSON). Convete datas com `datetime.fromisoformat` e insere no DB.

- GET /integration
  - Função: integration
  - Executa `backend/integration_db.py` para importar `data/raw/Technical Support Dataset.csv` para o DB.

- GET /recalculate_metrics
  - Função: recalculate_metrics
  - Executa `python3 data/etl.py` para regenerar `data/processed/metrics.json`.

## Workflow n8n — import, ativação e teste

1. Onde está o workflow
- Arquivo: `n8n/workflow.json`
- Webhook path configurado: `updated_status`
- Fluxo: Webhook (POST) → HTTP Request (PATCH para API /update_datetime_ticket/{{ $json.body.ticket }} com body `{ "close_time": "true" }`)

2. Como importar no n8n (UI)
- Abrir n8n (por ex. http://localhost:5678 ou via container).
- No painel lateral, ir em "Workflows" → botão "Import".
- Selecionar o arquivo `n8n/workflow.json` ou colar o JSON.
- Salvar e Ativar o workflow (toggle "Active" no topo).

3. Ajustes de URL / rede
- Se rodando via docker-compose, a API dentro do mesmo compose usa `http://api:5000` e n8n usa `http://n8n:5678` — o workflow já chama `http://api:5000/update_datetime_ticket/...`.
- Se rodando localmente (sem Docker), altere a URL do HTTP Request no workflow para `http://host.docker.internal:5000` ou `http://localhost:5000` conforme sua rede.

4. Teste manual (end-to-end)
- Ative o workflow no n8n.
- No terminal, faça um PATCH que mude o status para Closed (este PATCH deve fazer a API enviar POST ao webhook n8n):
```bash
curl -X PATCH -H "Content-Type: application/json" \
  -d '{"status":"Closed"}' \
  http://localhost:5000/tickets/123
```
- Verifique no n8n:
  - Webhook recebeu a requisição (History / Executions).
  - HTTP Request foi executado e retornou 200 para a API `/update_datetime_ticket/<ticket>`.

5. Troubleshooting rápido
- Se o webhook não receber nada:
  - Verifique logs da API e confirme a URL usada para POST (no container deve ser `http://n8n:5678/webhook/updated_status`).
  - Confirme que o workflow está ativo e o path é `updated_status`.
- Se o HTTP Request falhar:
  - Verifique a URL da API usada no node, e as opções de envio de body (bodyParameters).
  - Cheque permissões / CORS se estiver chamando cross-host.

## Visualização do workflow (screenshot)
![image](https://drive.google.com/uc?export=view&id=1r_FEKVtXmE7jx-dGScfM1ZjCCQ4qksQR)

## ETL (arquivo: data/etl.py)
- Entrada: `data/raw/Technical Support Dataset.csv`
- Principais etapas:
  1. Normaliza nomes de coluna (remove espaços e lower).
  2. Converte colunas de data (índices [7,8,9,12,14]).
  3. Calcula métricas: contagens, média de SLA (dias entre close_time e created_time), tickets por mês.
  4. Salva em `data/processed/metrics.json`.
- Executar manual:
```bash
python3 data/etl.py
```

## Trigger (arquivo: trigger.sh)
Sequência automática usada no docker-compose:
1. Espera API disponível (nc -z api 5000).
2. GET /integration (integra CSV → DB).
3. POST /new_tickets (insere seeds).
4. GET /recalculate_metrics (executa ETL).

## Comandos úteis
- Rodar integração manual:
```bash
python3 backend/integration_db.py
```
- Rodar ETL manual:
```bash
python3 data/etl.py
```
- Postar seeds manualmente:
```bash
curl -X POST -H "Content-Type: application/json" --data-binary '@backend/seeds/new_tickets.json' http://localhost:5000/new_tickets
```

## Arquivos-chave
- backend/main.py — API Flask.
- backend/integration_db.py — importa CSV para SQLite.
- backend/seeds/new_tickets.json — exemplo de tickets.
- data/etl.py — gera `data/processed/metrics.json`.
- data/processed/metrics.json — output do ETL.
- n8n/workflow.json — workflow do n8n (Webhook → PATCH /update_datetime_ticket).
- n8n/screenshot.png — screenshot do workflow.
- trigger.sh — orquestração inicial.
- docker-compose.yml & Dockerfile — containerização.

## Observações rápidas
- Atenção à comparação do status: no código atual há validação que aceita `Closed` (capitalizado) mas o disparo do webhook compara com `'closed'` (minúsculo). Recomenda-se unificar a checagem (ex.: comparar .lower()) para garantir que o webhook seja disparado corretamente.
- Em ambientes Docker, use os hostnames dos serviços definidos no compose (api, n8n). Em execução local, ajuste URLs para localhost/host.docker.internal.

Fim.