import asyncio
import logging
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Body
import json
from pydantic import BaseModel, validator
from typing import Union
import aiosqlite

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Event model
class Event(BaseModel):
    topic: str
    event_id: str
    timestamp: str
    source: str
    payload: Dict[str, Any]

    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('timestamp must be in ISO8601 format')

# Database setup
DATABASE_PATH = "dedup.db"

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS processed_events (
                topic TEXT,
                event_id TEXT,
                timestamp TEXT,
                source TEXT,
                payload TEXT,
                processed_at TEXT,
                PRIMARY KEY (topic, event_id)
            )
        ''')
        await db.commit()

async def is_event_processed(topic: str, event_id: str) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            'SELECT 1 FROM processed_events WHERE topic = ? AND event_id = ?',
            (topic, event_id)
        )
        return await cursor.fetchone() is not None

async def save_event(event: Event):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR IGNORE INTO processed_events
            (topic, event_id, timestamp, source, payload, processed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            event.topic,
            event.event_id,
            event.timestamp,
            event.source,
            json.dumps(event.payload),
            datetime.now(timezone.utc).isoformat()
        ))
        await db.commit()

# In-memory queue
event_queue = asyncio.Queue()

# Consumer task
async def consumer():
    while True:
        event = await event_queue.get()
        if await is_event_processed(event.topic, event.event_id):
            logger.info(f"Duplicate event detected: {event.topic}:{event.event_id}")
            stats["duplicate_dropped"] += 1
            event_queue.task_done()
            continue
        await save_event(event)
        logger.info(f"Processed event: {event.topic}:{event.event_id}")
        event_queue.task_done()

# Stats
stats = {
    "received": 0,
    "unique_processed": 0,
    "duplicate_dropped": 0,
    "topics": set(),
    "uptime": datetime.now(timezone.utc).isoformat()
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    task = asyncio.create_task(consumer())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

@app.post("/publish")
async def publish_event(events: List[Event]):
    # Accept list of events
    for event in events:
        await event_queue.put(event)
        stats["received"] += 1
        stats["topics"].add(event.topic)
    return {"status": "events queued"}

@app.get("/events")
async def get_events(topic: Optional[str] = Query(None)):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if topic:
            cursor = await db.execute(
                'SELECT topic, event_id, timestamp, source, payload FROM processed_events WHERE topic = ?',
                (topic,)
            )
        else:
            cursor = await db.execute(
                'SELECT topic, event_id, timestamp, source, payload FROM processed_events'
            )
        rows = await cursor.fetchall()
        events = []
        for row in rows:
            events.append({
                "topic": row[0],
                "event_id": row[1],
                "timestamp": row[2],
                "source": row[3],
                "payload": json.loads(row[4])
            })
        return events

@app.get("/stats")
async def get_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM processed_events')
        result = await cursor.fetchone()
        unique_processed = result[0] if result else 0
        stats["unique_processed"] = unique_processed
        stats["duplicate_dropped"] = stats["received"] - unique_processed
        stats["topics"] = list(stats["topics"])
        return stats