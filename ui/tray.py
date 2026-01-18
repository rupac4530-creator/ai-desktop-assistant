import os
import sys
import threading

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None
    Image = None

class TrayIcon:
    def __init__(self, on_start=None, on_stop=None, on_exit=None):
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_exit = on_exit
        self.icon = None
        self.running = False
    
    def _create_icon_image(self, color='green'):
        # Create a simple colored circle icon
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        colors = {
            'green': (0, 200, 0, 255),
            'red': (200, 0, 0, 255),
            'yellow': (200, 200, 0, 255),
            'blue': (0, 100, 200, 255)
        }
        fill = colors.get(color, colors['green'])
        
        # Draw filled circle
        draw.ellipse([4, 4, size-4, size-4], fill=fill, outline=(255, 255, 255, 255))
        
        # Draw AI text
        try:
            draw.text((size//2 - 10, size//2 - 8), "AI", fill=(255, 255, 255, 255))
        except:
            pass
        
        return image
    
    def _on_start(self, icon, item):
        self.running = True
        icon.icon = self._create_icon_image('green')
        if self.on_start:
            threading.Thread(target=self.on_start, daemon=True).start()
    
    def _on_stop(self, icon, item):
        self.running = False
        icon.icon = self._create_icon_image('yellow')
        if self.on_stop:
            self.on_stop()
    
    def _on_exit(self, icon, item):
        if self.on_exit:
            self.on_exit()
        icon.stop()
        sys.exit(0)
    
    def _on_status(self, icon, item):
        status = "Running" if self.running else "Stopped"
        print(f"[Tray] Status: {status}")
    
    def run(self):
        if not pystray or not Image:
            print("[Tray] pystray or PIL not available, running without tray icon")
            return False
        
        menu = pystray.Menu(
            pystray.MenuItem("Start Assistant", self._on_start),
            pystray.MenuItem("Stop Assistant", self._on_stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status", self._on_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._on_exit)
        )
        
        self.icon = pystray.Icon(
            "AI Assistant",
            self._create_icon_image('blue'),
            "AI Desktop Assistant",
            menu
        )
        
        print("[Tray] Starting system tray icon...")
        self.icon.run()
        return True
    
    def run_detached(self):
        # Run tray in background thread
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread
    
    def update_status(self, running):
        self.running = running
        if self.icon:
            self.icon.icon = self._create_icon_image('green' if running else 'yellow')


def create_tray(on_start=None, on_stop=None, on_exit=None):
    tray = TrayIcon(on_start, on_stop, on_exit)
    return tray


if __name__ == "__main__":
    # Test tray
    def on_start():
        print("Assistant started!")
    
    def on_stop():
        print("Assistant stopped!")
    
    def on_exit():
        print("Exiting...")
    
    tray = create_tray(on_start, on_stop, on_exit)
    tray.run()
