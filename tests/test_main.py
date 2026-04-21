import pytest
import asyncio
from datetime import datetime, timezone
import os
import tempfile
from fastapi.testclient import TestClient
from src.main import app, init_db, DATABASE_PATH

@pytest.fixture
def client():
    # Use a temporary database for tests
    global DATABASE_PATH
    original_db = DATABASE_PATH
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        DATABASE_PATH = tmp.name
    asyncio.run(init_db())
    with TestClient(app) as c:
        yield c
    os.unlink(DATABASE_PATH)
    DATABASE_PATH = original_db

def test_publish_single_event(client):
    event = {
        "topic": "test_topic",
        "event_id": "unique_id_1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "test_source",
        "payload": {"key": "value"}
    }
    response = client.post("/publish", json=[event])
    assert response.status_code == 200
    assert response.json() == {"status": "events queued"}

@pytest.mark.asyncio
async def test_publish_duplicate_event(client):
    event = {
        "topic": "test_topic",
        "event_id": "unique_id_2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "test_source",
        "payload": {"key": "value"}
    }
    # Publish twice
    client.post("/publish", json=[event])
    client.post("/publish", json=[event])
    # Wait for processing
    await asyncio.sleep(0.1)
    stats = client.get("/stats").json()
    assert stats["received"] == 2
    assert stats["unique_processed"] == 1
    assert stats["duplicate_dropped"] == 1

@pytest.mark.asyncio
async def test_get_events(client):
    event = {
        "topic": "test_topic",
        "event_id": "unique_id_3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "test_source",
        "payload": {"key": "value"}
    }
    client.post("/publish", json=[event])
    await asyncio.sleep(0.1)
    response = client.get("/events?topic=test_topic")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["event_id"] == "unique_id_3"

@pytest.mark.asyncio
async def test_get_stats(client):
    event = {
        "topic": "test_topic",
        "event_id": "unique_id_4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "test_source",
        "payload": {"key": "value"}
    }
    client.post("/publish", json=[event])
    await asyncio.sleep(0.1)
    stats = client.get("/stats").json()
    assert "received" in stats
    assert "unique_processed" in stats
    assert "duplicate_dropped" in stats
    assert "topics" in stats
    assert "uptime" in stats

def test_invalid_timestamp(client):
    event = {
        "topic": "test_topic",
        "event_id": "unique_id_5",
        "timestamp": "invalid",
        "source": "test_source",
        "payload": {"key": "value"}
    }
    response = client.post("/publish", json=[event])
    assert response.status_code == 422  # Validation error
@pytest.mark.asyncio
async def test_batch_events(client):
    events = [
        {
            "topic": "test_topic",
            "event_id": f"unique_id_{i}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "test_source",
            "payload": {"key": f"value_{i}"}
        } for i in range(5)
    ]
    response = client.post("/publish", json=events)
    assert response.status_code == 200
    await assert response.status_code == 200
    asyncio.sleep(0.1)
    stats = client.get("/stats").json()
    assert stats["received"] == 5
    assert stats["unique_processed"] == 5
@pytest.mark.asyncio
async def test_persistence_after_restart(client):
    # This test simulates restart by checking if events are still deduped
    # In a real scenario, you'd restart the app, but here we just check the db
    event = {
        "topic": "test_topic",
        "event_id": "unique_id_6",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "test_source",
        "payload": {"key": "value"}
    }
    client.post("/publish", json=[event])
    await asyncio.sleep(0.1)ish", json=[event])
    asyncio.sleep(0.1)
    # Simulate restart by posting again
    client.post("/publish", json=[event])
    asyncio.sleep(0.1)
    stats = client.get("/stats").json()
    assert stats["unique_processed"] == 1