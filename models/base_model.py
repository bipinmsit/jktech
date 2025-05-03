from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import as_declarative, declarative_base

Base = declarative_base()


@as_declarative()
class RequiredField:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
