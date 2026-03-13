"""
Folders CRUD routes
GET    /api/folders/          - list all folders
POST   /api/folders/          - create folder
GET    /api/folders/{id}      - get folder
PATCH  /api/folders/{id}      - rename folder
DELETE /api/folders/{id}      - delete folder
"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_folders: dict[str, dict] = {}


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    color: str = "#6366f1"


class FolderPatch(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class FolderRecord(BaseModel):
    id: str
    name: str
    parent_id: Optional[str]
    color: str
    created_at: str
    meeting_count: int = 0


@router.get("/", response_model=list[FolderRecord])
async def list_folders():
    return list(_folders.values())


@router.post("/", response_model=FolderRecord, status_code=201)
async def create_folder(body: FolderCreate):
    if body.parent_id and body.parent_id not in _folders:
        raise HTTPException(404, "Parent folder not found")
    folder_id = str(uuid.uuid4())
    record = FolderRecord(
        id=folder_id,
        name=body.name,
        parent_id=body.parent_id,
        color=body.color,
        created_at=datetime.utcnow().isoformat(),
    )
    _folders[folder_id] = record.model_dump()
    return record


@router.get("/{folder_id}", response_model=FolderRecord)
async def get_folder(folder_id: str):
    folder = _folders.get(folder_id)
    if not folder:
        raise HTTPException(404, "Folder not found")
    return folder


@router.patch("/{folder_id}", response_model=FolderRecord)
async def update_folder(folder_id: str, body: FolderPatch):
    folder = _folders.get(folder_id)
    if not folder:
        raise HTTPException(404, "Folder not found")
    if body.name is not None:
        folder["name"] = body.name
    if body.color is not None:
        folder["color"] = body.color
    return folder


@router.delete("/{folder_id}", status_code=204)
async def delete_folder(folder_id: str):
    if folder_id not in _folders:
        raise HTTPException(404, "Folder not found")
    del _folders[folder_id]
    # Orphan child folders
    for f in _folders.values():
        if f.get("parent_id") == folder_id:
            f["parent_id"] = None
