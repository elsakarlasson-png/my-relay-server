import asyncio
import json
import os
from typing import Dict, Optional
import websockets

# This stores the "Rooms" where phone and viewer meet
rooms: Dict[str, Dict[str, Optional[object]]] = {}

async def relay_message(room: str, target_role: str, message: dict):
    """Sends data from one person to the other in the same room"""
    target = rooms.get(room, {}).get(target_role)
    if target:
        try:
            await target.send(json.dumps(message))
        except:
            # If sending fails, the person probably disconnected
            rooms[room][target_role] = None

async def handler(ws):
    room, role = None, None
    try:
        # First message must be the 'join' message
        raw = await ws.recv()
        data = json.loads(raw)
        room = str(data.get("room", "default"))
        role = str(data.get("role", "")) # 'phone' or 'viewer'
        
        if role not in ["phone", "viewer"]:
            return

        # Create the room if it doesn't exist
        if room not in rooms:
            rooms[room] = {"phone": None, "viewer": None}
        
        # Save this connection
        rooms[room][role] = ws
        print(f"User joined: Room {room} as {role}")

        # Keep listening for frames or messages
        async for msg in ws:
            data = json.loads(msg)
            # If phone sends data, send it to viewer (and vice versa)
            target = "viewer" if role == "phone" else "phone"
            await relay_message(room, target, data)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup when someone leaves
        if room and role in rooms.get(room, {}):
            rooms[room][role] = None
            print(f"User left: Room {room}, Role {role}")

async def main():
    # Render gives us a port number. We MUST use it.
    port = int(os.environ.get("PORT", 8765))
    # '0.0.0.0' makes the server public to the internet
    async with websockets.serve(handler, "0.0.0.0", port, max_size=10 * 1024 * 1024):
        print(f"Server is running on port {port}...")
        await asyncio.Future() # Runs forever

if __name__ == "__main__":
    asyncio.run(main())