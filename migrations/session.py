from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv, dotenv_values

import os

# try loading from .env file (only when running locally)
try:
    config = dotenv_values(".env")
except FileNotFoundError:
    config = {}
# load secrets from /run/secrets/ (only when running in docker)
load_dotenv(dotenv_path="/run/secrets/prepit-secret")
load_dotenv()

DATABASE_URL = config.get("DB_URI") or os.getenv("DB_URI")

engine = create_engine(
    DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
