"""Tests for health check endpoints"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    assert "timestamp" in data


def test_config_check():
    """Test configuration check endpoint"""
    response = client.get("/api/health/config")
    assert response.status_code == 200
    data = response.json()
    assert "app_env" in data
    assert "vertex_ai_location" in data
    assert "rate_limit_per_minute" in data
