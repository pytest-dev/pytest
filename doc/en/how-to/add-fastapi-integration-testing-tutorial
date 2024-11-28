FastAPI Integration Testing Tutorial
==================================

This tutorial demonstrates how to write integration tests for FastAPI applications using pytest.

Prerequisites
------------

* Python 3.7+
* pytest
* FastAPI
* SQLAlchemy
* pytest-asyncio

Basic Setup
----------

First, let's set up the basic structure for integration testing. Create a ``tests`` directory in your project root with the following files::

    your_project/
    ├── app/
    │   ├── main.py
    │   ├── models.py
    │   └── dependencies.py
    └── tests/
        ├── conftest.py
        └── test_api.py

Setting Up the Test Database
~~~~~~~~~~~~~~~~~~~~~~~~~~

In ``conftest.py``, create fixtures for your test database:

.. code-block:: python

    import pytest
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import Base
    from app.dependencies import get_db

    # Use in-memory SQLite for tests
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    @pytest.fixture(scope="function")
    def db():
        Base.metadata.create_all(bind=engine)
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    @pytest.fixture(scope="function")
    def client(db):
        def override_get_db():
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()

Writing Integration Tests
-----------------------

In ``test_api.py``, create your test cases:

.. code-block:: python

    import pytest
    from app.auth import get_password_hash

    def test_register_user(client, db):
        response = client.post(
            "/register",
            json={
                "username": "testuser",
                "password": "testpassword",
                "email": "test@example.com",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data

    def test_login_user(client, db):
        # First create a user
        hashed_password = get_password_hash("testpassword")
        client.post(
            "/register",
            json={
                "username": "testuser",
                "password": "testpassword",
                "email": "test@example.com",
                "full_name": "Test User"
            }
        )

        # Then attempt login
        response = client.post(
            "/token",
            data={
                "username": "testuser",
                "password": "testpassword"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

Testing Protected Routes
~~~~~~~~~~~~~~~~~~~~~~

For endpoints that require authentication:

.. code-block:: python

    @pytest.fixture
    def authorized_client(client, db):
        # Create and login user
        client.post(
            "/register",
            json={
                "username": "testuser",
                "password": "testpassword",
                "email": "test@example.com",
                "full_name": "Test User"
            }
        )

        response = client.post(
            "/token",
            data={
                "username": "testuser",
                "password": "testpassword"
            }
        )

        access_token = response.json()["access_token"]
        client.headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return client

    def test_protected_route(authorized_client):
        response = authorized_client.get("/protected-resource")
        assert response.status_code == 200

Best Practices
-------------

1. **Isolated Test Database**: Always use a separate test database to avoid affecting production data.

2. **Clean State**: Use function-scoped fixtures to ensure each test starts with a clean database state.

3. **Dependency Override**: Override FastAPI dependencies to use test configurations instead of production ones.

4. **Error Cases**: Test both successful and error scenarios:

.. code-block:: python

    def test_login_invalid_credentials(client):
        response = client.post(
            "/token",
            data={
                "username": "nonexistent",
                "password": "wrong"
            }
        )
        assert response.status_code == 401

5. **Async Support**: For async endpoints, use ``pytest-asyncio``:

.. code-block:: python

    @pytest.mark.asyncio
    async def test_async_endpoint(client):
        response = await client.get("/async-endpoint")
        assert response.status_code == 200

Advanced Testing Scenarios
------------------------

Testing File Uploads
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def test_file_upload(client):
        files = {
            "file": ("test.txt", b"test content", "text/plain")
        }
        response = client.post("/upload", files=files)
        assert response.status_code == 200

Testing WebSocket Endpoints
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fastapi.testclient import TestClient
    from fastapi.websockets import WebSocket

    def test_websocket_endpoint(client):
        with client.websocket_connect("/ws") as websocket:
            websocket.send_text("Hello")
            data = websocket.receive_text()
            assert data == "Message received: Hello"

Running the Tests
---------------

Execute your tests using pytest::

    pytest tests/ -v --cov=app

This will run all tests and generate a coverage report for your application.
