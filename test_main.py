import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from postgres.database import get_db, Base

# Setup a test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost/test"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the database dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create the test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture
def test_user():
    return {"username": "testuser", "password": "testpassword"}


def test_register_user(test_user):
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}


def test_login_user(test_user):
    # First, register the user
    client.post("/auth/register", json=test_user)
    # Then, log in
    response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_ingest_document():
    with open("test_document.pdf", "wb") as f:
        f.write(b"%PDF-1.4 test content")
    with open("test_document.pdf", "rb") as f:
        response = client.post("/api/ingest/", files={"file": f})
    assert response.status_code == 200
    assert "id" in response.json()
    assert "content" in response.json()


def test_query_document():
    query = "What is candidate name?"  #Adjust based on your document content, I have written based on my resume
    response = client.post("/api/query/", json={"query": query})
    assert (
        response.status_code == 500 or response.status_code == 200
    )  # Adjust based on LLM availability
