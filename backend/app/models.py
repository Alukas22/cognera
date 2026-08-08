from sqlalchemy import Column, DateTime, Integer, String, func

from .database import Base


class ExampleModel(Base):
    __tablename__ = "example_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(length=255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
