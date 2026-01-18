# start_avatar_test.py — send a test animation trigger to VTube Studio via WebSocket
# Run: python start_avatar_test.py

import os
import json
from dotenv import load_dotenv
load_dotenv()

WS_URL = os.getenv("AVATAR_WS_URL", "ws://127.0.0.1:8001")

def test_animation(animation_name="wave"):
    print(f"Connecting to {WS_URL}...")
    try:
        import websocket
        ws = websocket.create_connection(WS_URL, timeout=5)
        print("Connected.")

        # VTube Studio API format (adjust if using different avatar software)
        payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "test_anim_1",
            "messageType": "HotkeyTriggerRequest",
            "data": {
                "hotkeyID": animation_name
            }
        }
        ws.send(json.dumps(payload))
        print(f"Sent animation trigger: {animation_name}")

        resp = ws.recv()
        print(f"Response: {resp}")
        ws.close()
        print("Test complete.")
    except ImportError:
        print("websocket-client not installed. Run: pip install websocket-client")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure VTube Studio is running with WebSocket enabled on the configured port.")

def test_talking_parameter(value=1.0):
    print(f"Sending talking parameter = {value}...")
    try:
        import websocket
        ws = websocket.create_connection(WS_URL, timeout=5)
        payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "test_param_1",
            "messageType": "InjectParameterDataRequest",
            "data": {
                "parameterValues": [
                    {"id": "talking", "value": value}
                ]
            }
        }
        ws.send(json.dumps(payload))
        resp = ws.recv()
        print(f"Response: {resp}")
        ws.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("== Avatar WebSocket Test ==\n")
    print("1) Testing animation trigger...")
    test_animation("dance")
    print("\n2) Testing talking parameter...")
    test_talking_parameter(1.0)
    import time; time.sleep(1)
    test_talking_parameter(0.0)
    print("\n== Done ==")
