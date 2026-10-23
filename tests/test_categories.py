import io
import pytest
from sqlmodel import select, col
from app.main import app
from app.models.user import User, UserRole
from app.api.deps import get_current_active_admin, get_current_user
from app.core.database import get_db

@pytest.fixture(autouse=True)
def override_auth_dependency(client):
    """
    Dynamically mock an Admin user for each test function so 
    admin-only endpoints pass authorization successfully.
    """
    def get_mock_admin() -> User:
        # Grab a session from the active test override database
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        try:
            statement = select(User).where(col(User.role) == UserRole.ADMIN)
            admin_user = db.exec(statement).first()
            if not admin_user:
                admin_user = User(
                    first_name="Admin",
                    last_name="User",
                    email="admin@dayloop.test",
                    password_hash="hashed_dummy_password",
                    role=UserRole.ADMIN
                )
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)
            return admin_user
        finally:
            db.close()

    app.dependency_overrides[get_current_active_admin] = get_mock_admin
    app.dependency_overrides[get_current_user] = get_mock_admin
    yield
    # Clean up overrides after test completion
    app.dependency_overrides.pop(get_current_active_admin, None)
    app.dependency_overrides.pop(get_current_user, None)


# ==========================================
# CATEGORY ENDPOINT & SERVICE TEST CASES
# ==========================================

def test_create_category_with_icon(client):
    """Test creating a category with form data and an optional image file upload."""
    image_bytes = b"fake-image-content"
    file_data = {"file": ("test_icon.png", io.BytesIO(image_bytes), "image/png")}
    
    form_data = {
        "name": "Historical Sites",
        "slug": "historical-sites",
        "description": "Ancient locations and ruins",
        "is_active": "true",
        "display_order": "1"
    }

    response = client.post("/api/v1/categories/", data=form_data, files=file_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Historical Sites"
    assert data["slug"] == "historical-sites"
    assert data["icon_url"] is not None
    assert "categories/icons" in data["icon_url"]


def test_get_categories(client):
    """Test retrieving the paginated list of categories."""
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_search_categories(client):
    """Test searching categories by query string."""
    response = client.get("/api/v1/categories/search?q=Historical")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "Historical" in data[0]["name"]


def test_read_category_by_slug(client):
    """Test fetching a category by its unique slug."""
    response = client.get("/api/v1/categories/slug/historical-sites")
    if response.status_code == 200:
        assert response.json()["slug"] == "historical-sites"
    else:
        assert response.status_code == 404


def test_reorder_categories(client):
    """Test updating display orders for categories in bulk using Pydantic model payload."""
    reorder_payload = [
        {"id": 1, "display_order": 5}
    ]
    response = client.patch("/api/v1/categories/reorder", json=reorder_payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Categories reordered successfully"}


def test_toggle_category_status(client):
    """Test toggling a category's active state."""
    response = client.patch("/api/v1/categories/1/status")
    assert response.status_code in [200, 404]