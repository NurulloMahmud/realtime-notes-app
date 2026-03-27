import uuid
import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.auth import decode_token
from app.services.connection_manager import manager
from app.services.notes import get_note_by_id, user_can_access, update_note

router = APIRouter(tags=["websocket"])


async def authenticate_ws(token: str) -> Optional[User]:
    async with AsyncSessionLocal() as db:
        payload = decode_token(token, expected_type="access")
        if not payload:
            return None
        try:
            user_id = uuid.UUID(payload["sub"])
        except (TypeError, ValueError):
            return None
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


@router.websocket("/ws/notes/{note_id}")
async def websocket_endpoint(note_id: uuid.UUID, websocket: WebSocket, token: str = Query(...)):
    user = await authenticate_ws(token)
    if not user:
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        note = await get_note_by_id(db, note_id)
        if not note:
            await websocket.close(code=4004)
            return
        can_access = await user_can_access(db, note, user.id)
        if not can_access:
            await websocket.close(code=4003)
            return

    await websocket.accept()
    await manager.connect(note_id, websocket, user)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "edit":
                content = data.get("content", "")
                cursor_position = data.get("cursor_position")

                if len(content) > 50000:
                    continue

                async with AsyncSessionLocal() as db:
                    note = await get_note_by_id(db, note_id)
                    if note:
                        await update_note(db, note, user.id, title=None, content=content)

                await manager.broadcast_edit(note_id, user, content, cursor_position, exclude=websocket)

            elif msg_type == "cursor":
                cursor_position = data.get("cursor_position")
                if cursor_position is not None:
                    await manager.broadcast_cursor(note_id, user, cursor_position, exclude=websocket)

    except WebSocketDisconnect:
        await manager.disconnect(note_id, websocket, user)
