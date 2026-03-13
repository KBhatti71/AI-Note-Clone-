"""
Meetings CRUD routes
GET  /api/meetings          - list all meetings
GET  /api/meetings/{id}     - get meeting detail
DELETE /api/meetings/{id}   - delete meeting
"""

import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# In-memory store for MVP (replace with PostgreSQL via SQLAlchemy in production)
_meetings: dict[str, dict] = {}


class MeetingCreate(BaseModel):
    title: str
    context: str = "work"


class MeetingRecord(BaseModel):
    id: str
    title: str
    context: str
    duration: Optional[float] = None
    created_at: str
    segment_count: int = 0
    high_importance_count: int = 0


@router.get("/", response_model=list[MeetingRecord])
async def list_meetings():
    return list(_meetings.values())


@router.get("/{meeting_id}", response_model=MeetingRecord)
async def get_meeting(meeting_id: str):
    meeting = _meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/", response_model=MeetingRecord, status_code=201)
async def create_meeting(body: MeetingCreate):
    meeting_id = str(uuid.uuid4())
    record = MeetingRecord(
        id=meeting_id,
        title=body.title,
        context=body.context,
        created_at=datetime.utcnow().isoformat(),
    )
    _meetings[meeting_id] = record.model_dump()
    return record


@router.delete("/{meeting_id}", status_code=204)
async def delete_meeting(meeting_id: str):
    if meeting_id not in _meetings:
        raise HTTPException(status_code=404, detail="Meeting not found")
    del _meetings[meeting_id]
