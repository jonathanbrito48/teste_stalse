from models import SessionLocal
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import time
import os
import pandas as pd


def ETL_integration_data():
    df = pd.read_csv('data/raw/Technical Support Dataset.csv', sep=',')

    df.columns = [col.replace(' ', '_').lower() for col in df.columns]

    ticket = {}
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        ticket[row_dict['ticket_id']] = row_dict

    session = SessionLocal()

    try:
        for record in ticket.values():
            sql = text("""
            INSERT OR REPLACE INTO tickets (status, ticket_id, priority, source, topic, agent_group, agent_name, created_time, expected_sla_to_resolve, expected_sla_to_first_response, first_response_time, sla_for_first_response, resolution_time, sla_for_resolution, close_time, agent_interactions, survey_results, product_group, support_level, country, latitude, longitude)
            VALUES (:status, :ticket_id, :priority, :source, :topic, :agent_group, :agent_name, :created_time, :expected_sla_to_resolve, :expected_sla_to_first_response, :first_response_time, :sla_for_first_response, :resolution_time, :sla_for_resolution, :close_time, :agent_interactions, :survey_results, :product_group, :support_level, :country, :latitude, :longitude)
            """)
            params = {
                'status': record.get('status'),
                'ticket_id': record.get('ticket_id'),
                'priority': record.get('priority'),
                'source': record.get('source'),
                'topic': record.get('topic'),
                'agent_group': record.get('agent_group'),
                'agent_name': record.get('agent_name'),
                'created_time': record.get('created_time'),
                'expected_sla_to_resolve': record.get('expected_sla_to_resolve'),
                'expected_sla_to_first_response': record.get('expected_sla_to_first_response'),
                'first_response_time': record.get('first_response_time'),
                'sla_for_first_response': record.get('sla_for_first_response'),
                'resolution_time': record.get('resolution_time'),
                'sla_for_resolution': record.get('sla_for_resolution'),
                'close_time': record.get('close_time'),
                'agent_interactions': record.get('agent_interactions'),
                'survey_results': record.get('survey_results'),
                'product_group': record.get('product_group'),
                'support_level': record.get('support_level'),
                'country': record.get('country'),
                'latitude': record.get('latitude'),
                'longitude': record.get('longitude')
            }
            session.execute(sql, params)

        session.commit()
        print("Dados integrados com sucesso!")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Erro ao integrar dados: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    ETL_integration_data()
