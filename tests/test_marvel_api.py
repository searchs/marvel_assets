import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from main import app, generate_marvel_hash, get_auth_params

# Create test client
client = TestClient(app)

# Sample API responses
MOCK_CHARACTERS_RESPONSE = {
    "data": {
        "results": [
            {"name": "Spider-Man", "comics": {"available": 2572}},
            {"name": "Iron Man", "comics": {"available": 2411}},
        ]
    }
}

MOCK_CHARACTER_RESPONSE = {
    "data": {
        "results": [
            {
                "id": 1,
                "name": "Spider-Man",
                "description": "Friendly neighborhood Spider-Man",
            }
        ]
    }
}

MOCK_COMICS_RESPONSE = {
    "data": {
        "results": [
            {"id": 1, "title": "Amazing Spider-Man"},
            {"id": 2, "title": "Fantastic Four"},
        ]
    }
}

MOCK_SERIES_RESPONSE = {
    "data": {
        "results": [
            {"id": 1, "title": "Spider-Man (2023)"},
            {"id": 2, "title": "X-Men (2023)"},
        ]
    }
}


# Test base endpoint
def test_base_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Marvel API app" in response.json()["message"]
    assert "version:" in response.json()


# Test hash generation
def test_generate_marvel_hash():
    test_ts = "1234567890"
    hash_result = generate_marvel_hash(test_ts)
    assert isinstance(hash_result, str)
    assert len(hash_result) == 32  # MD5 hash is 32 characters


# Test auth params generation
def test_get_auth_params():
    params = get_auth_params()
    assert "ts" in params
    assert "apikey" in params
    assert "hash" in params
    assert len(params["hash"]) == 32


# Test characters endpoint
@pytest.mark.asyncio
async def test_get_characters():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Configure mock
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_CHARACTERS_RESPONSE

        response = await client.get("/characters?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]["results"]) == 2
        assert data["data"]["results"][0]["name"] == "Spider-Man"


@pytest.mark.asyncio
async def test_get_characters_error():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 404

        response = await client.get("/characters")
        assert response.status_code == 404
        assert "Failed to fetch characters" in response.json()["detail"]


# Test single character endpoint
@pytest.mark.asyncio
async def test_get_character():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_CHARACTER_RESPONSE

        response = await client.get("/characters/1")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["results"][0]["name"] == "Spider-Man"


# Test comics endpoint
@pytest.mark.asyncio
async def test_get_comics():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_COMICS_RESPONSE

        response = await client.get("/comics?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["results"]) == 2
        assert data["data"]["results"][0]["title"] == "Amazing Spider-Man"


# Test series endpoint
@pytest.mark.asyncio
async def test_get_series():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_SERIES_RESPONSE

        response = await client.get("/series?limit=2&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["results"]) == 2
        assert data["data"]["results"][0]["title"] == "Spider-Man (2023)"


# Test characters_comics endpoint
@pytest.mark.asyncio
async def test_get_all_characters_comics():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_CHARACTERS_RESPONSE

        response = await client.get("/characters_comics?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert "Spider-Man" in data
        assert data["Spider-Man"] == 2572
        assert "Iron Man" in data
        assert data["Iron Man"] == 2411


# Test character_comics endpoint
@pytest.mark.asyncio
async def test_get_character_comics():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = MOCK_CHARACTERS_RESPONSE

        response = await client.get("/character_comics/Spider-Man")

        assert response.status_code == 200
        data = response.json()
        assert "Spider-Man" in data
        assert data["Spider-Man"] == 2572


@pytest.mark.asyncio
async def test_get_character_comics_not_found():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": {"results": []}}

        response = await client.get("/character_comics/NonExistentCharacter")

        assert response.status_code == 404
        assert "Character not found" in response.json()["detail"]
