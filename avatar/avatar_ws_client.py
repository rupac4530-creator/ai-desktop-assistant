import os
import json
import time
import threading
try:
    import websocket
except ImportError:
    websocket = None

WS_URL = os.getenv('AVATAR_WS_URL', 'ws://127.0.0.1:8001')
PLUGIN_NAME = "AI_Desktop_Assistant"
PLUGIN_DEVELOPER = "User"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), '.vts_token')

class AvatarWSClient:
    def __init__(self):
        self.ws = None
        self.authenticated = False
        self.auth_token = self._load_token()
        self._lock = threading.Lock()
        self._last_connect_attempt = 0
        self._connect_cooldown = 30  # seconds between retry attempts
        self._auth_failed = False  # permanent fail flag until restart
        
    def _load_token(self):
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return None
    
    def _save_token(self, token):
        try:
            with open(TOKEN_FILE, 'w') as f:
                f.write(token)
        except:
            pass

    def connect(self):
        if websocket is None:
            print("[Avatar] websocket-client not installed")
            return False
            
        # Don't retry if auth permanently failed
        if self._auth_failed:
            return False
            
        # Cooldown check
        now = time.time()
        if now - self._last_connect_attempt < self._connect_cooldown:
            return False
        self._last_connect_attempt = now
        
        try:
            self.ws = websocket.create_connection(WS_URL, timeout=5)
            print(f"[Avatar] Connected to VTube Studio at {WS_URL}")
            return self._authenticate()
        except Exception as e:
            print(f"[Avatar] Connection failed: {e}")
            return False

    def _send_request(self, request_type, data=None):
        if not self.ws:
            return None
        payload = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": f"req_{int(time.time()*1000)}",
            "messageType": request_type,
            "data": data or {}
        }
        with self._lock:
            try:
                self.ws.send(json.dumps(payload))
                resp = self.ws.recv()
                return json.loads(resp)
            except Exception as e:
                print(f"[Avatar] Request error: {e}")
                return None

    def _authenticate(self):
        # Try cached token first
        if self.auth_token:
            auth_resp = self._send_request("AuthenticationRequest", {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": PLUGIN_DEVELOPER,
                "authenticationToken": self.auth_token
            })
            if auth_resp and auth_resp.get("data", {}).get("authenticated"):
                self.authenticated = True
                print("[Avatar] Authenticated with cached token!")
                return True
        
        # Request new token (user must click Allow in VTube Studio)
        resp = self._send_request("AuthenticationTokenRequest", {
            "pluginName": PLUGIN_NAME,
            "pluginDeveloper": PLUGIN_DEVELOPER
        })
        if not resp:
            self._auth_failed = True
            return False

        if resp.get("messageType") == "AuthenticationTokenResponse":
            token = resp.get("data", {}).get("authenticationToken")
            if token:
                self.auth_token = token
                self._save_token(token)
                # Authenticate with new token
                auth_resp = self._send_request("AuthenticationRequest", {
                    "pluginName": PLUGIN_NAME,
                    "pluginDeveloper": PLUGIN_DEVELOPER,
                    "authenticationToken": token
                })
                if auth_resp and auth_resp.get("data", {}).get("authenticated"):
                    self.authenticated = True
                    print("[Avatar] Authentication successful!")
                    return True
                    
        print("[Avatar] Authentication failed - click Allow in VTube Studio popup, then restart")
        self._auth_failed = True
        return False

    def is_ready(self):
        """Check if connected and authenticated without triggering reconnect"""
        return self.ws is not None and self.authenticated

    def ensure_connected(self):
        if self.is_ready():
            return True
        return self.connect()

    def set_parameter(self, param_name, value, weight=1.0):
        # Only try if already connected - don't spam reconnects
        if not self.is_ready():
            return False
        resp = self._send_request("InjectParameterDataRequest", {
            "parameterValues": [{
                "id": param_name,
                "value": value,
                "weight": weight
            }]
        })
        return resp is not None

    def set_mouth_open(self, value):
        return self.set_parameter("MouthOpen", value)

    def trigger_hotkey(self, hotkey_id):
        if not self.is_ready():
            return False
        resp = self._send_request("HotkeyTriggerRequest", {
            "hotkeyID": hotkey_id
        })
        return resp is not None

    def get_hotkeys(self):
        if not self.ensure_connected():
            return []
        resp = self._send_request("HotkeysInCurrentModelRequest", {})
        if resp and "data" in resp:
            return resp["data"].get("availableHotkeys", [])
        return []

    def set_expression(self, expression_file):
        if not self.is_ready():
            return False
        resp = self._send_request("ExpressionActivationRequest", {
            "expressionFile": expression_file,
            "active": True
        })
        return resp is not None

    def animate_talking(self, duration=0.1, intensity=0.8):
        if not self.is_ready():
            return
        self.set_mouth_open(intensity)
        time.sleep(duration)
        self.set_mouth_open(0)

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
            self.authenticated = False


# Singleton instance
_client = None

def get_client():
    global _client
    if _client is None:
        _client = AvatarWSClient()
    return _client

def connect():
    return get_client().connect()

def set_mouth(value):
    return get_client().set_mouth_open(value)

def trigger_hotkey(hotkey_id):
    return get_client().trigger_hotkey(hotkey_id)

def set_expression(expr):
    return get_client().set_expression(expr)
