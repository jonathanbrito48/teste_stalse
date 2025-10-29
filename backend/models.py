from sqlalchemy import create_engine, MetaData, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from contextlib import contextmanager


engine = create_engine('sqlite:///backend/db.sqlite', echo=False)
metadata = MetaData()
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class tickets(Base):
    __tablename__ = 'tickets'
    ticket_id = Column(String, primary_key=True, nullable=False)
    status = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    source = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    agent_group = Column(String, nullable=False)
    agent_name = Column(String, nullable=False)
    created_time = Column(DateTime, nullable=False)
    expected_sla_to_resolve = Column(DateTime)
    expected_sla_to_first_response = Column(DateTime)
    first_response_time = Column(DateTime)
    sla_for_first_response = Column(String)
    resolution_time  = Column(DateTime)
    sla_for_resolution = Column(String)
    close_time = Column(DateTime)
    agent_interactions = Column(String)
    survey_results = Column(String)
    product_group = Column(String, nullable=False)
    support_level = Column(String, nullable=False)
    country = Column(String, nullable=False)
    latitude = Column(String)
    longitude = Column(String)
    def __repr__(self):
        return f"<ticket: '{self.ticket_id}')>"
    
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


@contextmanager
def get_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
