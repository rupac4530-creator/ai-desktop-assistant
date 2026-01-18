# test_avatar_ws.py — test WebSocket connection to VTube Studio
# Run: python tools/test_avatar_ws.py

import os
import json
from dotenv import load_dotenv
load_dotenv()

ws_url = os.getenv("AVATAR_WS_URL", "ws://127.0.0.1:8001")
print("Testing avatar WebSocket at:", ws_url)

try:
    import websocket
except ImportError:
    print("websocket-client not installed. Run: pip install websocket-client")
    exit(1)

import traceback

try:
    ws = websocket.create_connection(ws_url, timeout=5)
    print("Connected to avatar WebSocket")

    # Send a simple API state request (VTube Studio format)
    request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "test_conn",
        "messageType": "APIStateRequest"
    }
    ws.send(json.dumps(request))
    response = ws.recv()
    # Print truncated response safely
    if isinstance(response, (bytes, bytearray)):
        print(f"Received {len(response)} bytes response")
    else:
        print("Received response:", response[:1000])
    ws.close()
    print("WebSocket test complete")
except Exception as e:
    print("Failed to connect or communicate with avatar WebSocket:", str(e))
    traceback.print_exc()
    print("Make sure VTube Studio is running with WebSocket plugin enabled and accept any permission popup.")
