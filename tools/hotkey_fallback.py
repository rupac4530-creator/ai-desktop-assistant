"""
Python Hotkey Handler - Fallback when AHK doesn't work
Run this script to enable Ctrl+Alt+H, Ctrl+Alt+Space, Ctrl+Alt+T hotkeys
"""
import keyboard
import os
import sys
import subprocess
from pathlib import Path

print("=" * 50)
print("PYTHON HOTKEY HANDLER - ACTIVE")
print("=" * 50)
print("Registered hotkeys:")
print("  Ctrl+Alt+H     -> Toggle assistant")
print("  Ctrl+Alt+Space -> Push-to-talk")
print("  Ctrl+Alt+T     -> Test")
print("=" * 50)
print("Press Ctrl+C to exit")
print()

def on_ctrl_alt_h():
    print("[HOTKEY] Ctrl+Alt+H pressed!")
    # You can add your assistant toggle logic here
    os.system('msg * "Ctrl+Alt+H works! Python hotkey active."')

def on_ctrl_alt_space():
    print("[HOTKEY] Ctrl+Alt+Space pressed!")
    os.system('msg * "Ctrl+Alt+Space works! Python hotkey active."')

def on_ctrl_alt_t():
    print("[HOTKEY] Ctrl+Alt+T pressed!")
    os.system('msg * "Ctrl+Alt+T works! Python hotkey active."')

# Register hotkeys
keyboard.add_hotkey('ctrl+alt+h', on_ctrl_alt_h)
keyboard.add_hotkey('ctrl+alt+space', on_ctrl_alt_space)
keyboard.add_hotkey('ctrl+alt+t', on_ctrl_alt_t)

print("Hotkeys registered! Try pressing Ctrl+Alt+H now...")

# Keep running
try:
    keyboard.wait()
except KeyboardInterrupt:
    print("\nExiting hotkey handler...")
