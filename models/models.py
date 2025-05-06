from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
)
from models.base_model import RequiredField
from pgvector.sqlalchemy import Vector


# models/models.py
class Document(RequiredField):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    content = Column(Text)
    embedding = Column(Vector(384))  # Must match your embedding dimension
