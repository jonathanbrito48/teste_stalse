import faker
import json
import sqlalchemy as sa
from sqlalchemy import Table, Column, Integer, String, DateTime, Float, MetaData

import datetime as dt
from models import tickets, engine


def serialize_datetime(dattime_obj):
    return dt.datetime.isoformat(dattime_obj, sep=' ', timespec='milliseconds') if dattime_obj else None

metadata = MetaData()
fake = faker.Faker()

# fetch current max ticket_id from the DB and prepare next_ticket_id
def max_ticket_id():
    with engine.connect() as conn:
        max_ticket_id_stmt = sa.select(sa.func.max(tickets.ticket_id))
        max_ticket_id = conn.execute(max_ticket_id_stmt).scalar() or 0
    return int(max_ticket_id)

max_id = max_ticket_id()


def generate_new_ticket_data(id):
    return {
        'status': fake.random_element(elements=('open', 'in_progress', 'closed', 'resolved')),
        'ticket_id': id,
        'priority': fake.random_element(elements=('low', 'medium', 'high', 'urgent')),
        'source': fake.random_element(elements=('email', 'phone', 'chat', 'web')),
        'topic': fake.sentence(nb_words=6),
        'agent_group': fake.random_element(elements=('Level 1', 'Level 2', 'Level 3')),
        'agent_name': fake.name(),
        'created_time': serialize_datetime(fake.date_time_this_year()),
        'expected_sla_to_resolve': serialize_datetime(fake.date_time_this_year()),
        'expected_sla_to_first_response': serialize_datetime(fake.date_time_this_year()),
        'first_response_time': serialize_datetime(fake.date_time_this_year()),
        'sla_for_first_response': fake.random_int(min=1, max=48),
        'resolution_time': serialize_datetime(fake.date_time_this_year()),
        'sla_for_resolution': fake.random_int(min=1, max=168),
        'close_time': serialize_datetime(fake.date_time_this_year()),
        'agent_interactions': fake.random_int(min=1, max=10),
        'survey_results': fake.random_element(elements=('satisfied', 'neutral', 'dissatisfied')),
        'product_group': fake.random_element(elements=('Software', 'Hardware', 'Services')),
        'support_level': fake.random_element(elements=('Basic', 'Premium', 'Enterprise')),
        'country': fake.country(),
        'latitude': float(fake.latitude()),
        'longitude': float(fake.longitude()),
    }

new_tickets = []

for _ in range(20):
    max_id += 1
    ticket_data = generate_new_ticket_data(max_id)
    new_tickets.append(ticket_data)

with open('/app/backend/seeds/new_tickets.json', 'w') as f:
    json.dump(new_tickets, f, default=str, indent=4)