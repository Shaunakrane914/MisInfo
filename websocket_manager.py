"""
Project Aegis - WebSocket Connection Manager
Handles all active WebSocket connections to the dashboard for real-time updates
"""

from fastapi import WebSocket
from typing import List
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections for real-time dashboard updates"""
    
    def __init__(self):
        """Initialize the connection manager with an empty list of connections"""
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """
        Accept a new WebSocket connection and add it to the active connections list.
        
        Args:
            websocket (WebSocket): The WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection established. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from the active connections list.
        
        Args:
            websocket (WebSocket): The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket connection removed. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """
        Broadcast a message to all active WebSocket connections.
        
        Args:
            message (dict): The message to broadcast as a dictionary
        """
        # Convert the message dictionary to a JSON string
        json_message = json.dumps(message)
        
        # Loop through all active connections
        for connection in self.active_connections.copy():  # Use copy to avoid modification during iteration
            try:
                # Send the JSON message to the connection
                await connection.send_text(json_message)
                logger.debug(f"Message sent to WebSocket connection")
            except Exception as e:
                # If an exception occurs, the connection is dead
                logger.warning(f"Failed to send message to WebSocket connection: {e}")
                # Remove the dead connection from the active connections list
                self.disconnect(connection)