from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# from utils.config import env
# Update DATABASE_URL with your actual database details and SSL certificate path
# Define your database URL
DATABASE_URL = "postgresql://postgres:postgres@localhost/jktyre"
engine = create_engine(DATABASE_URL)
Session_Local = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = Session_Local()
    try:
        yield db
    finally:
        db.close()
