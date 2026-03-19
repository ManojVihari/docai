from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///docai.db")
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class APIVersion(Base):
    __tablename__ = "api_versions"

    id = Column(Integer, primary_key=True, index=True)
    api_name = Column(String)
    version = Column(Integer)
    commit_hash = Column(String)
    content = Column(Text)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)
