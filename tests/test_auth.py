import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_db

# Use an in-memory SQLite database for testing with StaticPool
sqlite_url = "sqlite://"
test_engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def override_get_db():
    with Session(test_engine) as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    """Create a clean database schema before each test and drop it afterwards."""
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture
def client():
    return TestClient(app)


# --- Tests for /register ---

def test_register_success(client):
    response = client.post(
        "/api/v1/auth/register",  # Adjust prefix if your router is mounted differently (e.g., "/register")
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "securepassword123",
            "role": "user"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "john.doe@example.com"
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["role"] == "user"
    assert "id" in data
    assert "password_hash" not in data
    assert "password" not in data

def test_register_duplicate_email(client):
    payload = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "password": "password123"
    }
    # First registration
    client.post("/api/v1/auth/register", json=payload)
    
    # Second registration with same email
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered in the system."


# --- Tests for /login ---

def test_login_success(client):
    # Setup user
    client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Alice",
            "last_name": "Brown",
            "email": "alice@example.com",
            "password": "mypassword"
        }
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "alice@example.com",
            "password": "mypassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


# --- Tests for /refresh ---

def test_refresh_token_success(client):
    # Register and Login to acquire a valid refresh token
    user_payload = {
        "first_name": "Bob",
        "last_name": "Builder",
        "email": "bob@example.com",
        "password": "password123"
    }
    client.post("/api/v1/auth/register", json=user_payload)
    
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]}
    )
    refresh_token = login_response.json()["refresh_token"]

    # Request new access token using refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] == refresh_token
    assert data["token_type"] == "bearer"

def test_refresh_token_invalid(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.jwt.token.string"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate refresh token"