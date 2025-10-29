from flask import Flask, jsonify, request
import os
import pandas as pd
import json
from sqlalchemy import create_engine, select, update, insert
from models import tickets, engine
import requests
import datetime as dt

app = Flask(__name__)

# substitua a criação atual do engine por algo baseado em caminho absoluto
db_file = os.path.join(os.path.dirname(__file__), "db.sqlite")
engine = create_engine(f"sqlite:///{os.path.abspath(db_file)}", echo=False)

@app.route('/tickets', methods=['GET'])
def list_tickets():
    db = engine.connect() 
    stmt = select(tickets)
    tickets_db = db.execute(stmt).fetchall()
    tickets_json = [dict(row._mapping) for row in tickets_db]
    return jsonify(tickets_json)


@app.route('/metrics', methods=['GET'])
def get_metrics():
    with open('data/processed/metrics.json','r') as f:
        metrics = json.load(f)

    return metrics


@app.route('/tickets/<int:ticket>', methods=['PATCH'])
def update_status_ticket(ticket):
    new_status = request.json.get('status')
    if not new_status:
        return jsonify({"error": "Invalid status"}), 400
    elif new_status.lower() not in ['open', 'in progress', 'closed', 'resolved']:
        return jsonify({"error": "Status must be one of: Open, In Progress, Closed, Resolved"}), 400

    db = engine.connect()
    stmt = update(tickets).where(tickets.ticket_id == ticket).values(status=new_status.title())
    db.execute(stmt)
    db.commit()

    # Disparar webhook quando status for "closed" (case-insensitive)
    if new_status.lower() == 'closed':
        webhook_url = os.environ.get('N8N_WEBHOOK_URL', 'http://n8n:5678/webhook/updated_status')
        payload = {'ticket': ticket, 'status': new_status}
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception:
            pass

    return jsonify({"message": "Status updated successfully"}), 200

@app.route('/update_datetime_ticket/<int:ticket>', methods=['PATCH'])
def update_time_ticket(ticket):
    update_datetime = request.json.get('close_time')

    if update_datetime == 'true':
        close_time = dt.datetime.now() - dt.timedelta(hours=3)
        db = engine.connect()
        stmt = update(tickets).where(tickets.ticket_id == ticket).values(close_time=close_time)
        db.execute(stmt)
        db.commit()
        return jsonify({"message": "datetime updated successfully","ticket": ticket,"close_time": close_time}), 200
    
    return jsonify()

@app.route('/new_tickets', methods=['POST'])
def create_ticket():
    ticket_data = request.json
    db = engine.connect()
    for item in ticket_data:
        
        params = {
            'status': item.get('status'),
            'ticket_id': item.get('ticket_id'),
            'priority': item.get('priority'),
            'source': item.get('source'),
            'topic': item.get('topic'),
            'agent_group': item.get('agent_group'),
            'agent_name': item.get('agent_name'),
            'created_time': dt.datetime.fromisoformat(item.get('created_time')),
            'expected_sla_to_resolve': dt.datetime.fromisoformat(item.get('expected_sla_to_resolve')),
            'expected_sla_to_first_response': dt.datetime.fromisoformat(item.get('expected_sla_to_first_response')),
            'first_response_time': dt.datetime.fromisoformat(item.get('first_response_time')),
            'sla_for_first_response': item.get('sla_for_first_response'),
            'resolution_time': dt.datetime.fromisoformat(item.get('resolution_time')),
            'sla_for_resolution': item.get('sla_for_resolution'),
            'close_time': dt.datetime.fromisoformat(item.get('close_time')),
            'agent_interactions': item.get('agent_interactions'),
            'survey_results': item.get('survey_results'),
            'product_group': item.get('product_group'),
            'support_level': item.get('support_level'),
            'country': item.get('country'),
            'latitude': item.get('latitude'),
            'longitude': item.get('longitude')
        }
        
        stmt = insert(tickets).values(**params)
        db.execute(stmt)
        db.commit()
    return jsonify({"message": "Ticket created successfully"}), 201

@app.route('/integration', methods=['GET'])
def integration():
    os.system('python3 backend/integration_db.py')
    return jsonify({"message": "Integration endpoint"}), 200

@app.route('/recalculate_metrics', methods=['GET'])
def recalculate_metrics():
    os.system('python3 data/etl.py')
    return jsonify({"message": "Recalculation of metrics triggered"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)