"""
Full-text search across notes and meetings.
GET /api/search/?q=<query>&types=notes,meetings
"""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

# Import in-memory stores lazily to avoid circular deps
def _get_notes():
    from api.routes.notes import _notes
    return _notes

def _get_meetings():
    from api.routes.meetings import _meetings
    return _meetings


def _score(text: str, query: str) -> float:
    """Simple relevance score: count of (lowercased) term occurrences."""
    q = query.lower()
    t = text.lower()
    return t.count(q) / max(len(t.split()), 1)


@router.get("/")
async def search(
    q: str = Query(..., min_length=1),
    types: str = Query("notes,meetings"),
    limit: int = Query(20, ge=1, le=100),
):
    include_notes = "notes" in types
    include_meetings = "meetings" in types
    results = []

    if include_notes:
        for note in _get_notes().values():
            haystack = f"{note.get('title', '')} {note.get('content', '')} {' '.join(note.get('tags', []))}"
            if q.lower() in haystack.lower():
                results.append({
                    "type": "note",
                    "id": note["id"],
                    "title": note.get("title", ""),
                    "snippet": _snippet(note.get("content", ""), q),
                    "score": _score(haystack, q),
                    "created_at": note.get("created_at", ""),
                })

    if include_meetings:
        for meeting in _get_meetings().values():
            haystack = meeting.get("title", "")
            if q.lower() in haystack.lower():
                results.append({
                    "type": "meeting",
                    "id": meeting["id"],
                    "title": meeting.get("title", ""),
                    "snippet": meeting.get("title", ""),
                    "score": _score(haystack, q),
                    "created_at": meeting.get("created_at", ""),
                })

    results.sort(key=lambda r: r["score"], reverse=True)
    return {"query": q, "results": results[:limit], "total": len(results)}


def _snippet(content: str, query: str, context: int = 80) -> str:
    """Return a short snippet of content around the first match."""
    idx = content.lower().find(query.lower())
    if idx == -1:
        return content[:context]
    start = max(0, idx - context // 2)
    end = min(len(content), idx + len(query) + context // 2)
    snippet = content[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(content):
        snippet = snippet + "…"
    return snippet
