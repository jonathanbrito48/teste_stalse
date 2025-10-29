# Teste Stalse

Resumo
Projeto de exemplo que expõe uma API Flask para tickets, integra dados CSV ao SQLite, recalcula métricas via ETL e integra com um workflow n8n.

Índice
- Requisitos
- Execução (rápida)
- Rotas da API
- Workflow n8n
- ETL (data/etl.py)
- Trigger (trigger.sh)
- Comandos úteis
- Arquivos-chave
- Notas rápidas

## Requisitos
- Python 3.11 (ou compatível)
- Docker & docker-compose (opcional, recomendado)

## Execução

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
O compose levanta os serviços:
- api (Flask)
- n8n (n8n)
- trigger (executa trigger.sh)

## Rotas da API (arquivo: backend/main.py)

GET /tickets
- Função: list_tickets
- Retorna todos os registros da tabela `tickets` como JSON.
- Exemplo:
```bash
curl http://localhost:5000/tickets
```

GET /metrics
- Função: get_metrics
- Retorna o JSON gerado pelo ETL: `data/processed/metrics.json`.
- Exemplo:
```bash
curl http://localhost:5000/metrics
```

PATCH /tickets/<int:ticket>
- Função: update_status_ticket
- Body esperado: `{ "status": "Open" }`
- Validações: somente `Open`, `In Progress`, `Closed`, `Resolved`.
- Atualiza status no DB.
- Efeito colateral: se o novo status for `closed` (atenção: no código atual a checagem compara string minúscula `'closed'`), a API faz POST para o webhook n8n em `http://n8n:5678/webhook/updated_status`.
- Exemplo:
```bash
curl -X PATCH -H "Content-Type: application/json" -d '{"status":"Closed"}' http://localhost:5000/tickets/123
```

PATCH /update_datetime_ticket/<int:ticket>
- Função: update_time_ticket
- Body esperado: `{ "close_time": "true" }`
- Se `close_time == "true"`, define `close_time` do ticket como `data atual` e atualiza o DB.
- Exemplo:
```bash
curl -X PATCH -H "Content-Type: application/json" -d '{"close_time":"true"}' http://localhost:5000/update_datetime_ticket/123
```

POST /new_tickets
- Função: create_ticket
- Recebe lista de tickets JSON (ver `backend/seeds/new_tickets.json`).
- Converte datas com `datetime.fromisoformat` e insere no DB.
- Exemplo:
```bash
curl -X POST -H "Content-Type: application/json" --data-binary '@backend/seeds/new_tickets.json' http://localhost:5000/new_tickets
```

GET /integration
- Função: integration
- Executa o script `backend/integration_db.py` que importa `data/raw/Technical Support Dataset.csv` para o DB.
- Exemplo:
```bash
curl http://localhost:5000/integration
```

GET /recalculate_metrics
- Função: recalculate_metrics
- Executa `python3 data/etl.py` para regenerar `data/processed/metrics.json`.
- Exemplo:
```bash
curl http://localhost:5000/recalculate_metrics
```

## Workflow n8n (arquivo: n8n/workflow.json)
- Contém:
  - Webhook (path `updated_status`) que recebe POSTs.
  - HTTP Request que faz PATCH para:
    - URL: `http://api:5000/update_datetime_ticket/{{ $json.body.ticket }}`
    - Body: `{ "close_time": "true" }`
- Fluxo resumido:
  1. A API, ao definir um ticket como `closed`, faz POST para `http://n8n:5678/webhook/updated_status`.
  2. n8n recebe o webhook e envia um PATCH para a API para ajustar `close_time` do ticket automaticamente.

## ETL (arquivo: data/etl.py)
- Entrada: `data/raw/Technical Support Dataset.csv`
- Principais passos:
  1. Normaliza nomes de coluna (remove espaços e passa para lowercase).
  2. Converte colunas de data (índices [7,8,9,12,14] no CSV) para datetime.
  3. Calcula métricas:
     - Contagens por categorias.
     - Média de SLA: diferença em dias entre `close_time` e `created_time`.
     - Tickets por mês (`ano_mes_ticket`) agrupados por categorias.
  4. Salva o resultado em `data/processed/metrics.json`.
- Executar manual:
```bash
python3 data/etl.py
```

## Trigger (arquivo: trigger.sh)
Script usado pelo serviço `trigger` no docker-compose para orquestrar uma sequência:
1. Espera até a API estar disponível (verifica host `api` na porta 5000).
2. GET /integration -> integra CSV ao DB.
3. POST /new_tickets -> insere tickets de seed (`backend/seeds/new_tickets.json`).
4. GET /recalculate_metrics -> executa o ETL e atualiza `data/processed/metrics.json`.

Trechos importantes:
```bash
while ! nc -z api 5000; do sleep 2; done
curl -X GET http://api:5000/integration
curl -X POST --header 'Content-Type: application/json' \
     --data-binary '@backend/seeds/new_tickets.json' \
     http://api:5000/new_tickets
curl -X GET http://api:5000/recalculate_metrics
```

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
- backend/main.py — API Flask e rotas.
- backend/integration_db.py — integra CSV para SQLite.
- backend/seeds/new_tickets.json — tickets de exemplo para POST /new_tickets.
- data/etl.py — gera `data/processed/metrics.json`.
- data/processed/metrics.json — output do ETL (consumido por /metrics).
- n8n/workflow.json — workflow que recebe webhook e chama a API.
- trigger.sh — orquestra import + seeds + recálculo.
- docker-compose.yml & Dockerfile — containerização.

## Notas rápidas
- Banco: SQLite via SQLAlchemy; arquivo em `backend/db.sqlite`.
- Atenção: no código atual há comparação de status com string minúscula `'closed'` e validação que usa `Closed` — pode causar comportamento inesperado ao acionar o webhook n8n.
- Ajustes em formatos de data ou nomes de coluna devem ser feitos em `data/etl.py` e `backend/integration_db.py`.

Fim.