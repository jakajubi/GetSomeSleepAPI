from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class SleepResult(Base):
    __tablename__ = "sleep_results"

    id = Column(Integer, primary_key=True, index=True)
    sleep_seconds = Column(Integer)
    quality = Column(Integer)
