import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional
from fastapi import WebSocket
from app.models.user import User


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[tuple[WebSocket, User]]] = {}
        self._pending_saves: dict[str, asyncio.Task] = {}

    def _key(self, note_id: uuid.UUID) -> str:
        return str(note_id)

    async def connect(self, note_id: uuid.UUID, websocket: WebSocket, user: User):
        key = self._key(note_id)
        if key not in self._connections:
            self._connections[key] = []
        self._connections[key].append((websocket, user))
        await self._broadcast_presence(note_id, user, "joined", exclude=websocket)

    async def disconnect(self, note_id: uuid.UUID, websocket: WebSocket, user: User):
        key = self._key(note_id)
        if key in self._connections:
            self._connections[key] = [(ws, u) for ws, u in self._connections[key] if ws != websocket]
            if not self._connections[key]:
                del self._connections[key]
        await self._broadcast_presence(note_id, user, "left")

    async def broadcast_cursor(self, note_id: uuid.UUID, user: User, cursor_position: int, exclude: WebSocket):
        message = json.dumps({
            "type": "cursor",
            "user_id": str(user.id),
            "username": user.username,
            "cursor_position": cursor_position,
        })
        await self._send_to_all(note_id, message, exclude=exclude)

    async def broadcast_edit(self, note_id: uuid.UUID, user: User, content: str, cursor_position: Optional[int], exclude: WebSocket):
        message = json.dumps({
            "type": "update",
            "user_id": str(user.id),
            "username": user.username,
            "content": content,
            "cursor_position": cursor_position,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        await self._send_to_all(note_id, message, exclude=exclude)

    async def _broadcast_presence(self, note_id: uuid.UUID, user: User, status: str, exclude: Optional[WebSocket] = None):
        message = json.dumps({
            "type": "presence",
            "user_id": str(user.id),
            "username": user.username,
            "status": status,
        })
        await self._send_to_all(note_id, message, exclude=exclude)

    async def _send_to_all(self, note_id: uuid.UUID, message: str, exclude: Optional[WebSocket] = None):
        key = self._key(note_id)
        for ws, _ in self._connections.get(key, []):
            if ws != exclude:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass

    def get_online_users(self, note_id: uuid.UUID) -> list[dict]:
        key = self._key(note_id)
        return [{"user_id": str(u.id), "username": u.username} for _, u in self._connections.get(key, [])]

    def schedule_save(self, note_id: uuid.UUID, save_coro, delay: float = 1.0):
        key = self._key(note_id)
        if key in self._pending_saves:
            self._pending_saves[key].cancel()

        async def _delayed():
            await asyncio.sleep(delay)
            await save_coro
            self._pending_saves.pop(key, None)

        task = asyncio.create_task(_delayed())
        self._pending_saves[key] = task


manager = ConnectionManager()
