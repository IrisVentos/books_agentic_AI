from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    title = Column(String)
    author = Column(String)
    price = Column(Float)
    description = Column(Text)
    isbn = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    ai_summary = Column(Text, nullable=True)
    ai_processed_at = Column(DateTime, nullable=True)
