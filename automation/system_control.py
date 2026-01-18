import os
import subprocess
import webbrowser
import time

try:
    import pyautogui
    pyautogui.FAILSAFE = True
except ImportError:
    pyautogui = None

# Load allowlist and dangerous actions
ALLOWLIST_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'allowlist.txt')
DANGEROUS_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'dangerous_actions.txt')

def load_list(path):
    try:
        with open(path, 'r') as f:
            return [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]
    except:
        return []

ALLOWLIST = load_list(ALLOWLIST_PATH)
DANGEROUS_ACTIONS = load_list(DANGEROUS_PATH)

# Common apps and their paths/commands
APP_REGISTRY = {
    'youtube': 'https://www.youtube.com',
    'google': 'https://www.google.com',
    'chatgpt': 'https://chat.openai.com',
    'github': 'https://github.com',
    'gmail': 'https://mail.google.com',
    'whatsapp': 'https://web.whatsapp.com',
    'twitter': 'https://twitter.com',
    'x': 'https://x.com',
    'reddit': 'https://reddit.com',
    'notepad': 'notepad.exe',
    'calculator': 'calc.exe',
    'paint': 'mspaint.exe',
    'explorer': 'explorer.exe',
    'cmd': 'cmd.exe',
    'powershell': 'powershell.exe',
    'vscode': 'code',
    'chrome': 'chrome',
    'firefox': 'firefox',
    'edge': 'msedge',
    'spotify': 'spotify',
    'discord': 'discord',
    'steam': 'steam',
    'vlc': 'vlc',
}

class SystemControl:
    def __init__(self):
        self.last_action = None
        self.action_log = []
    
    def _log_action(self, action, params, result):
        entry = {'time': time.strftime('%Y-%m-%d %H:%M:%S'), 'action': action, 'params': params, 'result': result}
        self.action_log.append(entry)
        print(f"[Action] {action}: {params} -> {result}")
    
    def _is_dangerous(self, action):
        return action.lower() in DANGEROUS_ACTIONS
    
    def _is_allowed(self, app):
        if not ALLOWLIST:
            return True  # If no allowlist, allow all
        return app.lower() in ALLOWLIST
    
    def open_app(self, app_name):
        if not app_name:
            return "No app specified"
        
        app_lower = app_name.lower().strip()
        
        # Check registry first
        if app_lower in APP_REGISTRY:
            target = APP_REGISTRY[app_lower]
            if target.startswith('http'):
                return self.open_url(target)
            else:
                return self._launch_app(target)
        
        # Try as URL
        if app_lower.startswith('http'):
            return self.open_url(app_name)
        
        # Try as direct command
        return self._launch_app(app_name)
    
    def _launch_app(self, app):
        try:
            subprocess.Popen(app, shell=True)
            self._log_action('open_app', app, 'success')
            return f"Opened {app}"
        except Exception as e:
            self._log_action('open_app', app, f'failed: {e}')
            return f"Failed to open {app}: {e}"
    
    def open_url(self, url):
        try:
            if not url.startswith('http'):
                url = 'https://' + url
            webbrowser.open(url)
            self._log_action('open_url', url, 'success')
            return f"Opened {url}"
        except Exception as e:
            self._log_action('open_url', url, f'failed: {e}')
            return f"Failed to open URL: {e}"
    
    def search_google(self, query):
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return self.open_url(url)
    
    def search_youtube(self, query):
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        return self.open_url(url)
    
    def type_text(self, text):
        if not pyautogui:
            return "pyautogui not available"
        try:
            time.sleep(0.5)  # Give user time to focus window
            pyautogui.typewrite(text, interval=0.02)
            self._log_action('type_text', text[:50], 'success')
            return f"Typed: {text[:50]}..."
        except Exception as e:
            return f"Failed to type: {e}"
    
    def press_key(self, key):
        if not pyautogui:
            return "pyautogui not available"
        try:
            pyautogui.press(key)
            self._log_action('press_key', key, 'success')
            return f"Pressed {key}"
        except Exception as e:
            return f"Failed to press key: {e}"
    
    def hotkey(self, *keys):
        if not pyautogui:
            return "pyautogui not available"
        try:
            pyautogui.hotkey(*keys)
            self._log_action('hotkey', keys, 'success')
            return f"Pressed {'+'.join(keys)}"
        except Exception as e:
            return f"Failed hotkey: {e}"
    
    def copy(self):
        return self.hotkey('ctrl', 'c')
    
    def paste(self):
        return self.hotkey('ctrl', 'v')
    
    def take_screenshot(self, filename=None):
        if not pyautogui:
            return "pyautogui not available"
        try:
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"
            path = os.path.join(os.path.expanduser('~'), 'Pictures', filename)
            pyautogui.screenshot(path)
            self._log_action('screenshot', path, 'success')
            return f"Screenshot saved to {path}"
        except Exception as e:
            return f"Failed to take screenshot: {e}"
    
    def adjust_volume(self, direction='up', amount=10):
        try:
            if direction == 'up':
                for _ in range(amount // 2):
                    pyautogui.press('volumeup')
            elif direction == 'down':
                for _ in range(amount // 2):
                    pyautogui.press('volumedown')
            elif direction == 'mute':
                pyautogui.press('volumemute')
            return f"Volume {direction}"
        except:
            return "Volume control failed"
    
    def shutdown(self, confirm=False):
        if not confirm:
            return "CONFIRMATION_REQUIRED: Shutdown requires confirmation. Say 'confirm shutdown' to proceed."
        try:
            subprocess.run(['shutdown', '/s', '/t', '60'], check=True)
            return "Shutting down in 60 seconds. Run 'shutdown /a' to cancel."
        except Exception as e:
            return f"Shutdown failed: {e}"
    
    def restart(self, confirm=False):
        if not confirm:
            return "CONFIRMATION_REQUIRED: Restart requires confirmation."
        try:
            subprocess.run(['shutdown', '/r', '/t', '60'], check=True)
            return "Restarting in 60 seconds."
        except Exception as e:
            return f"Restart failed: {e}"
    
    def lock_screen(self):
        try:
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'])
            return "Screen locked"
        except:
            return "Failed to lock screen"
    
    def sleep(self):
        try:
            subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0', '1', '0'])
            return "Going to sleep"
        except:
            return "Failed to sleep"


# Convenience functions
_system = None

def get_system():
    global _system
    if _system is None:
        _system = SystemControl()
    return _system

def open_app(app):
    return get_system().open_app(app)

def open_url(url):
    return get_system().open_url(url)

def search(query, engine='google'):
    if engine == 'youtube':
        return get_system().search_youtube(query)
    return get_system().search_google(query)
