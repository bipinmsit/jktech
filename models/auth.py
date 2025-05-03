from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime

# from mysql.database import Base
from models.base_model import RequiredField


class User(RequiredField):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)


class Token(RequiredField):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    access_token = Column(String(2048), nullable=False)
    refresh_token = Column(String(2048), nullable=False)
    access_token_expiry = Column(DateTime, nullable=False)
    refresh_token_expiry = Column(DateTime, nullable=False)
