"""
Tests for map config and search endpoints.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_map_config_without_credentials():
    with patch("app.services.map_service.get_mappls_credentials", return_value=None):
        resp = client.get("/api/map/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "osm"
    assert data["token"] is None


def test_map_config_with_credentials():
    with patch(
        "app.services.map_service.get_mappls_credentials",
        return_value={"token": "test-token", "auth_type": "rest_key"},
    ):
        resp = client.get("/api/map/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "mappls"
    assert data["token"] == "test-token"
    assert data["auth_type"] == "rest_key"


def test_map_search_requires_query():
    resp = client.get("/api/map/search")
    assert resp.status_code == 422


def test_map_search_returns_suggestions_shape():
    with patch(
        "app.services.map_service.search_places",
        return_value=[{
            "name": "Indiranagar",
            "address": "Bengaluru, Karnataka",
            "latitude": 12.9784,
            "longitude": 77.6408,
        }],
    ):
        resp = client.get("/api/map/search?q=Indiranagar")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["name"] == "Indiranagar"
