"""
WebSocket connection management and real-time events
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types for WebSocket communication"""
    # Session events
    SESSION_STARTED = "session.started"
    SESSION_STOPPED = "session.stopped"
    SESSION_ERROR = "session.error"
    SESSION_STATUS_UPDATE = "session.status_update"

    # Metrics events
    METRICS_UPDATE = "metrics.update"
    GPU_USAGE = "gpu.usage"
    MEMORY_USAGE = "memory.usage"

    # Terminal events
    TERMINAL_OUTPUT = "terminal.output"
    TERMINAL_INPUT = "terminal.input"
    TERMINAL_RESIZE = "terminal.resize"

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
    WORKFLOW_STEP_FAILED = "workflow.step_failed"
    WORKFLOW_COMPLETED = "workflow.completed"

    # Collaboration events
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    CURSOR_UPDATE = "cursor.update"

    # System events
    CONNECTION_ESTABLISHED = "connection.established"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class WebSocketEvent:
    """WebSocket event with standardized format"""

    def __init__(
        self,
        event_type: EventType,
        data: dict,
        user_id: str | None = None,
        workspace_id: str | None = None,
        session_id: str | None = None,
    ):
        self.event_type = event_type
        self.data = data
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.session_id = session_id
        self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        """Convert event to JSON"""
        return json.dumps({
            "type": self.event_type.value,
            "data": self.data,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
        })

    @classmethod
    def from_json(cls, json_str: str) -> "WebSocketEvent":
        """Create event from JSON"""
        data = json.loads(json_str)
        return cls(
            event_type=EventType(data["type"]),
            data=data.get("data", {}),
            user_id=data.get("user_id"),
            workspace_id=data.get("workspace_id"),
            session_id=data.get("session_id"),
        )


class ConnectionManager:
    """Manage WebSocket connections and broadcasting"""

    def __init__(self):
        # Store connections by workspace_id
        self.active_connections: Dict[str, List[Dict]] = {}  # workspace_id -> [{user_id, websocket}, ...]
        self.user_connections: Dict[str, WebSocket] = {}  # user_id -> websocket

    async def connect(self, websocket: WebSocket, workspace_id: str, user_id: str):
        """Register new connection"""
        await websocket.accept()

        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = []

        self.active_connections[workspace_id].append({
            "user_id": user_id,
            "websocket": websocket,
        })
        self.user_connections[user_id] = websocket

        logger.info(f"User {user_id} connected to workspace {workspace_id}")

    def disconnect(self, workspace_id: str, user_id: str):
        """Unregister connection"""
        if workspace_id in self.active_connections:
            self.active_connections[workspace_id] = [
                conn for conn in self.active_connections[workspace_id]
                if conn["user_id"] != user_id
            ]

            if not self.active_connections[workspace_id]:
                del self.active_connections[workspace_id]

        if user_id in self.user_connections:
            del self.user_connections[user_id]

        logger.info(f"User {user_id} disconnected from workspace {workspace_id}")

    async def broadcast_to_workspace(self, workspace_id: str, event: WebSocketEvent):
        """Broadcast event to all users in workspace"""
        if workspace_id not in self.active_connections:
            return

        disconnected = []
        for conn in self.active_connections[workspace_id]:
            try:
                await conn["websocket"].send_text(event.to_json())
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.append(conn["user_id"])

        # Clean up disconnected users
        for user_id in disconnected:
            self.disconnect(workspace_id, user_id)

    async def send_to_user(self, user_id: str, event: WebSocketEvent):
        """Send event to specific user"""
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_text(event.to_json())
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")

    def get_workspace_users(self, workspace_id: str) -> List[str]:
        """Get list of active users in workspace"""
        if workspace_id not in self.active_connections:
            return []

        return [conn["user_id"] for conn in self.active_connections[workspace_id]]

    def get_active_connections_count(self, workspace_id: str) -> int:
        """Get count of active connections in workspace"""
        if workspace_id not in self.active_connections:
            return 0

        return len(self.active_connections[workspace_id])


# Global connection manager instance
manager = ConnectionManager()
