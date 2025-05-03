import uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from models.base_model import RequiredField
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Float
from pgvector.sqlalchemy import Vector


class Document(RequiredField):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    # embedding = Column(ARRAY(Float), nullable=False)
    embedding = Column(Vector(384))  # Adjust the dimension to match your embedding size
