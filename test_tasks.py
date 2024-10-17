# test_tasks.py
import pytest
from fastapi.testclient import TestClient
from tasks_main import app, users_collection, tasks_collection
import uuid

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Setup the database for testing."""
    # Clear users and tasks collections before tests
    users_collection.delete_many({})
    tasks_collection.delete_many({})

    # Register a test user and an admin user
    users_collection.insert_many([
        {
            "username": "user",
            "email": "user@example.com",
            "password": "hashed_password",  # Use a hash if you need to
            "is_admin": False
        },
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": "hashed_password",  # Use a hash if you need to
            "is_admin": True
        }
    ])
    yield  # This is where the tests will run
    # Cleanup after tests
    users_collection.delete_many({})
    tasks_collection.delete_many({})


@pytest.fixture(scope="module")
def user_token():
    """Fixture to get a user access token."""
    response = client.post("/login", json={"username": "user", "password": "userpass"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    """Fixture to get an admin access token."""
    response = client.post("/login", json={"username": "admin", "password": "adminpass"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_register_user():
    """Test user registration."""
    response = client.post("/register", json={
        "username": "new_user",
        "email": "new_user@example.com",
        "password": "new_user_pass",
        "is_admin": False
    })
    assert response.status_code == 200
    assert response.json() == {"message": "User successfully registered"}


def test_login_user():
    """Test user login endpoint."""
    response = client.post("/login", json={"username": "user", "password": "userpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_create_task(user_token):
    """Test creating a task."""
    task_data = {"title": "New Task", "details": "Task description", "due_date": "2024-12-31T12:00:00"}
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.post("/tasks", json=task_data, headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Task created successfully"
    assert "task_id" in response_data


def test_get_task(user_token):
    """Test retrieving a task."""
    task_data = {"title": "Task to Get", "details": "Retrieve this task", "due_date": "2024-12-31T12:00:00"}
    headers = {"Authorization": f"Bearer {user_token}"}
    create_response = client.post("/tasks", json=task_data, headers=headers)
    assert create_response.status_code == 200
    task_id = create_response.json()["task_id"]

    response = client.get(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == task_data["title"]
    assert response.json()["details"] == task_data["details"]


def test_update_task(user_token):
    """Test updating a task."""
    task_data = {"title": "Task to Update", "details": "Original description", "due_date": "2024-12-31T12:00:00"}
    headers = {"Authorization": f"Bearer {user_token}"}
    create_response = client.post("/tasks", json=task_data, headers=headers)
    assert create_response.status_code == 200
    task_id = create_response.json()["task_id"]

    updated_data = {"title": "Updated Task", "details": "Updated description", "due_date": "2025-01-01T12:00:00"}
    response = client.put(f"/tasks/{task_id}", json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Task updated successfully"


def test_delete_task(user_token):
    """Test deleting a task."""
    task_data = {"title": "Task to Delete", "details": "Will be deleted", "due_date": "2024-12-31T12:00:00"}
    headers = {"Authorization": f"Bearer {user_token}"}
    create_response = client.post("/tasks", json=task_data, headers=headers)
    assert create_response.status_code == 200
    task_id = create_response.json()["task_id"]

    response = client.delete(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Task deleted successfully"

    # Verify the task is deleted
    get_response = client.get(f"/tasks/{task_id}", headers=headers)
    assert get_response.status_code == 404
