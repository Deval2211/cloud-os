"""
WebSocket routes for real-time events
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import logging
import json

from auth.db import get_db_session, get_user_by_id
from auth.utils import verify_token
from websocket.manager import manager, EventType, WebSocketEvent
from models import Workspace

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


async def get_user_from_token(token: str):
    """Extract user from WebSocket token"""
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return user_id
    except:
        return None


@router.websocket("/ws/workspace/{workspace_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    workspace_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db_session)
):
    """
    WebSocket endpoint for workspace real-time events
    
    Query params:
    - token: JWT access token for authentication
    
    Example connection:
    ws://localhost:8000/ws/workspace/workspace-id?token=jwt-token
    """
    # Authenticate user
    user_id = await get_user_from_token(token)
    if not user_id:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # Verify workspace exists and user has access
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        await websocket.close(code=1008, reason="Workspace not found")
        return

    if workspace.owner_id != user_id and not workspace.is_active:
        await websocket.close(code=1008, reason="Access denied")
        return

    # Accept connection
    await manager.connect(websocket, workspace_id, user_id)

    # Send connection established event
    connection_event = WebSocketEvent(
        event_type=EventType.CONNECTION_ESTABLISHED,
        data={
            "message": "Connected to workspace",
            "workspace_id": workspace_id,
            "active_users": manager.get_workspace_users(workspace_id),
        },
        user_id=user_id,
        workspace_id=workspace_id,
    )
    await websocket.send_text(connection_event.to_json())

    # Broadcast user joined event
    user_joined_event = WebSocketEvent(
        event_type=EventType.USER_JOINED,
        data={
            "user_id": user_id,
            "active_users": manager.get_workspace_users(workspace_id),
        },
        workspace_id=workspace_id,
    )
    await manager.broadcast_to_workspace(workspace_id, user_joined_event)

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                event = WebSocketEvent.from_json(data)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {user_id}")
                error_event = WebSocketEvent(
                    event_type=EventType.ERROR,
                    data={"error": "Invalid JSON format"},
                    user_id=user_id,
                )
                await websocket.send_text(error_event.to_json())
                continue

            # Ensure user_id matches token
            event.user_id = user_id
            event.workspace_id = workspace_id

            # Handle different event types
            if event.event_type in [
                EventType.TERMINAL_INPUT,
                EventType.TERMINAL_RESIZE,
                EventType.WORKFLOW_STARTED,
            ]:
                # Personal events - send only to initiator
                await manager.send_to_user(user_id, event)

            elif event.event_type in [
                EventType.SESSION_STARTED,
                EventType.SESSION_STOPPED,
                EventType.METRICS_UPDATE,
                EventType.TERMINAL_OUTPUT,
                EventType.WORKFLOW_STEP_COMPLETED,
                EventType.WORKFLOW_COMPLETED,
                EventType.CURSOR_UPDATE,
            ]:
                # Broadcast events - send to all users in workspace
                await manager.broadcast_to_workspace(workspace_id, event)

            else:
                # Unknown event type
                logger.warning(f"Unknown event type: {event.event_type}")

            logger.debug(f"Event {event.event_type.value} from {user_id}")

    except WebSocketDisconnect:
        manager.disconnect(workspace_id, user_id)

        # Broadcast user left event
        user_left_event = WebSocketEvent(
            event_type=EventType.USER_LEFT,
            data={
                "user_id": user_id,
                "active_users": manager.get_workspace_users(workspace_id),
            },
            workspace_id=workspace_id,
        )
        await manager.broadcast_to_workspace(workspace_id, user_left_event)
        logger.info(f"User {user_id} disconnected from workspace {workspace_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(workspace_id, user_id)
