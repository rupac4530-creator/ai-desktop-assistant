# E:\ai_desktop_assistant\ui\hud.py
"""
Lightweight HUD overlay using Tkinter.
Shows: Listening state, current plan step, errors.
Toggle with Ctrl+Alt+U
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class HUDOverlay:
    """Lightweight always-on-top HUD overlay."""
    
    def __init__(self):
        self.root = None
        self.visible = False
        self._thread = None
        self._running = False
        
        # State
        self.listening = False
        self.current_step = ""
        self.total_steps = 0
        self.step_num = 0
        self.error_msg = ""
        self.status_text = "Ready"
        
        # UI elements
        self._status_label = None
        self._step_label = None
        self._error_label = None
        self._listening_indicator = None
    
    def _create_window(self):
        """Create the HUD window."""
        self.root = tk.Tk()
        self.root.title("AI Assistant")
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.85)
        self.root.overrideredirect(True)  # No window decorations
        
        # Position in top-right corner
        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"280x100+{screen_w - 300}+20")
        
        # Dark theme
        self.root.configure(bg='#1e1e1e')
        
        # Main frame
        frame = tk.Frame(self.root, bg='#1e1e1e', padx=10, pady=8)
        frame.pack(fill='both', expand=True)
        
        # Header with listening indicator
        header = tk.Frame(frame, bg='#1e1e1e')
        header.pack(fill='x')
        
        self._listening_indicator = tk.Canvas(header, width=12, height=12, bg='#1e1e1e', highlightthickness=0)
        self._listening_indicator.pack(side='left', padx=(0, 8))
        self._draw_indicator(False)
        
        self._status_label = tk.Label(
            header, text="Ready", 
            fg='#ffffff', bg='#1e1e1e',
            font=('Segoe UI', 10, 'bold')
        )
        self._status_label.pack(side='left')
        
        # Step progress
        self._step_label = tk.Label(
            frame, text="", 
            fg='#888888', bg='#1e1e1e',
            font=('Segoe UI', 9),
            anchor='w'
        )
        self._step_label.pack(fill='x', pady=(5, 0))
        
        # Error message
        self._error_label = tk.Label(
            frame, text="",
            fg='#ff6b6b', bg='#1e1e1e',
            font=('Segoe UI', 9),
            anchor='w',
            wraplength=260
        )
        self._error_label.pack(fill='x', pady=(3, 0))
        
        # Make window draggable
        self.root.bind('<Button-1>', self._start_drag)
        self.root.bind('<B1-Motion>', self._do_drag)
        
        # Start update loop
        self._update_ui()
    
    def _draw_indicator(self, active: bool):
        """Draw the listening indicator circle."""
        self._listening_indicator.delete('all')
        color = '#4caf50' if active else '#555555'
        self._listening_indicator.create_oval(2, 2, 10, 10, fill=color, outline=color)
    
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
    
    def _do_drag(self, event):
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")
    
    def _update_ui(self):
        """Update UI elements from state."""
        if not self.root:
            return
        
        try:
            # Update listening indicator
            self._draw_indicator(self.listening)
            
            # Update status
            status = "🎤 Listening..." if self.listening else self.status_text
            self._status_label.config(text=status)
            
            # Update step progress
            if self.total_steps > 0:
                self._step_label.config(text=f"Step {self.step_num}/{self.total_steps}: {self.current_step}")
            else:
                self._step_label.config(text="")
            
            # Update error
            if self.error_msg:
                self._error_label.config(text=f"⚠ {self.error_msg}")
            else:
                self._error_label.config(text="")
            
            # Schedule next update
            self.root.after(100, self._update_ui)
        except tk.TclError:
            pass  # Window was closed
    
    def _run_loop(self):
        """Run the Tkinter main loop in a thread."""
        self._create_window()
        self._running = True
        self.root.mainloop()
        self._running = False
    
    def show(self):
        """Show the HUD overlay."""
        if self._running:
            if self.root:
                self.root.deiconify()
            self.visible = True
            return
        
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.visible = True
        time.sleep(0.2)  # Wait for window to appear
    
    def hide(self):
        """Hide the HUD overlay."""
        if self.root:
            try:
                self.root.withdraw()
            except:
                pass
        self.visible = False
    
    def toggle(self):
        """Toggle HUD visibility."""
        if self.visible:
            self.hide()
        else:
            self.show()
    
    def destroy(self):
        """Close the HUD."""
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
        self.root = None
        self._running = False
    
    # State update methods
    def set_listening(self, listening: bool):
        self.listening = listening
    
    def set_status(self, status: str):
        self.status_text = status
    
    def set_step(self, step_num: int, total: int, description: str):
        self.step_num = step_num
        self.total_steps = total
        self.current_step = description
    
    def set_error(self, error: Optional[str]):
        self.error_msg = error or ""
    
    def clear_step(self):
        self.step_num = 0
        self.total_steps = 0
        self.current_step = ""


# Global instance
_hud = None


def get_hud() -> HUDOverlay:
    """Get or create the global HUD instance."""
    global _hud
    if _hud is None:
        _hud = HUDOverlay()
    return _hud


def show_hud():
    get_hud().show()


def hide_hud():
    get_hud().hide()


def toggle_hud():
    get_hud().toggle()


# Quick test
if __name__ == "__main__":
    print("Testing HUD overlay...")
    hud = HUDOverlay()
    hud.show()
    
    # Simulate states
    time.sleep(1)
    hud.set_listening(True)
    time.sleep(1)
    hud.set_listening(False)
    hud.set_status("Processing...")
    time.sleep(1)
    hud.set_step(2, 5, "Opening browser")
    time.sleep(1)
    hud.set_step(3, 5, "Searching YouTube")
    time.sleep(1)
    hud.set_error("Connection timeout")
    time.sleep(2)
    hud.set_error(None)
    hud.set_step(5, 5, "Complete!")
    time.sleep(2)
    
    print("Test complete. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        hud.destroy()
