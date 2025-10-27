from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

user = os.getenv('DATABASE_USERNAME')
password = os.getenv('DATABASE_PASSWORD')
host = os.getenv('DATABASE_HOSTNAME')
dbname = os.getenv('DATABASE_NAME')

SQLALCHEMY_DATABASE_URL_FORMAT = f"postgresql://{user}:{password}@{host}/{dbname}"
# SQLALCHEMY_DATABASE_URL_FORMAT = f"postgresql://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOSTNAME')}/{os.getenv('DATABASE_NAME')}"


SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL_FORMAT


engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
