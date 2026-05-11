import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
 
load_dotenv()
 
DATABASE_URL: str = os.getenv("DATABASE_URL")
 
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment variables.")
 

engine = create_engine(DATABASE_URL, pool_pre_ping=True)  #(pool_size=5, max_overflow=10)
 

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
