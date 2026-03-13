"""
Notes CRUD routes
GET    /api/notes/            - list notes (filter by folder_id / meeting_id)
POST   /api/notes/            - create note
GET    /api/notes/{id}        - get note
PATCH  /api/notes/{id}        - update note
DELETE /api/notes/{id}        - delete note
POST   /api/notes/{id}/move   - move to different folder
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()

_notes: dict[str, dict] = {}


class NoteCreate(BaseModel):
    title: str
    content: str = ""
    folder_id: Optional[str] = None
    meeting_id: Optional[str] = None
    tags: list[str] = []


class NotePatch(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None


class NoteMove(BaseModel):
    folder_id: Optional[str] = None


class NoteRecord(BaseModel):
    id: str
    title: str
    content: str
    folder_id: Optional[str]
    meeting_id: Optional[str]
    tags: list[str]
    created_at: str
    updated_at: str
    word_count: int = 0


@router.get("/", response_model=list[NoteRecord])
async def list_notes(
    folder_id: Optional[str] = Query(None),
    meeting_id: Optional[str] = Query(None),
):
    notes = list(_notes.values())
    if folder_id:
        notes = [n for n in notes if n.get("folder_id") == folder_id]
    if meeting_id:
        notes = [n for n in notes if n.get("meeting_id") == meeting_id]
    return notes


@router.post("/", response_model=NoteRecord, status_code=201)
async def create_note(body: NoteCreate):
    note_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    record = NoteRecord(
        id=note_id,
        title=body.title,
        content=body.content,
        folder_id=body.folder_id,
        meeting_id=body.meeting_id,
        tags=body.tags,
        created_at=now,
        updated_at=now,
        word_count=len(body.content.split()),
    )
    _notes[note_id] = record.model_dump()
    return record


@router.get("/{note_id}", response_model=NoteRecord)
async def get_note(note_id: str):
    note = _notes.get(note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    return note


@router.patch("/{note_id}", response_model=NoteRecord)
async def update_note(note_id: str, body: NotePatch):
    note = _notes.get(note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    if body.title is not None:
        note["title"] = body.title
    if body.content is not None:
        note["content"] = body.content
        note["word_count"] = len(body.content.split())
    if body.tags is not None:
        note["tags"] = body.tags
    note["updated_at"] = datetime.utcnow().isoformat()
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str):
    if note_id not in _notes:
        raise HTTPException(404, "Note not found")
    del _notes[note_id]


@router.post("/{note_id}/move", response_model=NoteRecord)
async def move_note(note_id: str, body: NoteMove):
    note = _notes.get(note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    note["folder_id"] = body.folder_id
    note["updated_at"] = datetime.utcnow().isoformat()
    return note
