import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import AppConfig

config = AppConfig()

engine = create_engine(config.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
Base = declarative_base()


def prepare_database_connection() -> None:
    logger = logging.getLogger("cognera.database")
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        logger.info("Database connection prepared")
