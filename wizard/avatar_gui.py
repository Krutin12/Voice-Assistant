#!/usr/bin/env python3
"""
Wizard Voice Assistant - Anime VTuber GUI
A floating, animated anime VTuber character that serves as the visual face of the assistant.
Features:
  - Completely transparent background (floating directly on desktop)
  - Animated character with state-based poses (idle, listening, speaking, thinking, gestures)
  - Lip sync (mouth movement) when speaking
  - Floating stylized status text overlay matching an anime/cyberpunk aesthetic
  - Draggable VTuber window
"""

import tkinter as tk
import threading
import time
import math
import os
import sys
from pathlib import Path

# Try to import PIL for image handling
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("⚠️  Pillow not installed. Install with: pip install Pillow")
    print("   Avatar will fall back to text-mode.")

class AvatarState:
    """Enum-like class for avatar states"""
    IDLE = "idle"
    LISTENING = "listening"
    SPEAKING = "speaking"
    THINKING = "thinking"
    STARTUP = "startup"
    ERROR = "error"

class AvatarGUI:
    """Floating anime VTuber window for the Wizard Voice Assistant."""
    
    def __init__(self, width=400, height=450):
        self.width = width
        self.height = height
        self.state = AvatarState.STARTUP
        self.status_text = "Initializing system..."
        self.command_text = ""
        self.running = False
        self.root = None
        self._thread = None
        self._drag_data = {"x": 0, "y": 0}
        
        # VTuber Animation variables
        self._animation_phase = 0.0
        self._speaking_toggle = False
        self._speaking_timer = 0
        
        # Transparent key color (#00ff00 is standard green screen)
        # Windows Tkinter uses this to make the window fully transparent!
        self.trans_color = '#00ff00'
        
        self.images = {}
        self.current_photo = None

    def _find_sprite_images(self):
        """Locate the anime sprite images in the generated brain directory"""
        # Mapping base states to prefixes we generated
        prefix_mapping = {
            AvatarState.IDLE: "anime_idle",
            AvatarState.LISTENING: "anime_listening",
            AvatarState.THINKING: "anime_thinking",
            AvatarState.SPEAKING: "anime_speaking",
            AvatarState.STARTUP: "anime_idle",
            AvatarState.ERROR: "anime_thinking"
        }
        
        home = Path.home()
        gemini_brain = home / ".gemini" / "antigravity" / "brain"
        
        found_paths = {}
        if gemini_brain.exists():
            for conv_dir in sorted(gemini_brain.iterdir(), reverse=True):
                if not conv_dir.is_dir(): continue
                for state, prefix in prefix_mapping.items():
                    if state not in found_paths:
                        for img_file in conv_dir.glob(f"{prefix}*.png"):
                            found_paths[state] = str(img_file)
                            break
                if len(found_paths) >= 4:
                    break
        
        return found_paths

    def _load_images(self, target_size=(350, 350)):
        """Load and resize all state images"""
        if not HAS_PIL: return
        paths = self._find_sprite_images()
        
        for state, path in paths.items():
            try:
                img = Image.open(path)
                # Resize keeping aspect ratio
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Check background color and ensure it fits our transparent key
                # The images generated are already green screen!
                
                self.images[state] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading {state} image: {e}")

    def start(self):
        """Start the VTuber GUI in a background thread"""
        if self.running: return
        self.running = True
        self._thread = threading.Thread(target=self._run_gui, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the VTuber GUI"""
        self.running = False
        if self.root:
            try:
                self.root.after(0, self.root.destroy)
            except Exception: pass
            
    def set_state(self, state: str):
        """Update the VTuber state (changes pose)"""
        self.state = state
        # Reset labels initially based on pose
        defaults = {
            AvatarState.IDLE: "Ready",
            AvatarState.LISTENING: "Listening to command...",
            AvatarState.SPEAKING: "Speaking...",
            AvatarState.THINKING: "Processing request...",
            AvatarState.STARTUP: "Booting cyber-wizard...",
            AvatarState.ERROR: "System malfuncion."
        }
        if not self.command_text:
            self.status_text = defaults.get(state, "...")
            
    def set_status_text(self, text: str):
        self.status_text = text
        
    def set_command_text(self, text: str):
        self.command_text = text

    def _run_gui(self):
        self.root = tk.Tk()
        self.root.title("Wizard VTuber")
        self.root.geometry(f"{self.width}x{self.height}")
        
        # Transparent overlay mode
        try:
            self.root.attributes('-transparentcolor', self.trans_color)
        except Exception:
            pass # Fails on non-Windows sometimes
        
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True) # Remove windows borders
        
        # Center bottom right
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - self.width - 20
        y = screen_h - self.height - 60
        self.root.geometry(f"+{x}+{y}")
        
        self.root.configure(bg=self.trans_color)
        
        # Load Images
        self._load_images()
        
        # Create UI
        self._build_ui()
        
        # Drag binds
        self.avatar_canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.avatar_canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.status_label.bind("<ButtonPress-1>", self._on_drag_start)
        self.status_label.bind("<B1-Motion>", self._on_drag_motion)
        
        self._animate()
        
        try:
            self.root.mainloop()
        except: pass

    def _build_ui(self):
        # Character canvas (transparent green background)
        self.avatar_canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=350,
            bg=self.trans_color,
            highlightthickness=0
        )
        self.avatar_canvas.pack()
        
        # Character Image item
        if self.images:
            start_img = self.images.get(AvatarState.STARTUP) or list(self.images.values())[0]
            self.char_ref = self.avatar_canvas.create_image(self.width//2, 175, image=start_img)
        else: # Fallback
            self.char_ref = self.avatar_canvas.create_text(self.width//2, 175, text="🧙\n(No Image)", font=("Segoe UI Emoji", 48), justify="center")
            
        # Context UI background styling (cyberpunk/modern dark)
        self.ui_frame = tk.Frame(self.root, bg="#111116", bd=2, highlightbackground="#00E5FF", highlightcolor="#00E5FF", highlightthickness=1)
        self.ui_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Status
        self.status_label = tk.Label(
            self.ui_frame,
            text="",
            bg="#111116",
            fg="#00E5FF",
            font=("Segoe UI", 11, "bold"),
            wraplength=340
        )
        self.status_label.pack(pady=(4, 2))
        
        # Command
        self.command_label = tk.Label(
            self.ui_frame,
            text="",
            bg="#111116",
            fg="#E040FB",
            font=("Segoe UI", 9, "italic"),
            wraplength=340
        )
        self.command_label.pack(pady=(0, 4))

    def _animate(self):
        if not self.running or not self.root: return
        try:
            self._animation_phase += 0.1
            
            # --- Character State & Lip Sync ---
            if self.images:
                img_state = self.state
                
                # Lip sync simulation - alternate mouth open/closed when speaking
                if self.state == AvatarState.SPEAKING:
                    self._speaking_timer += 1
                    # Swap frame every 4 ticks (~130ms) for talking animation
                    if self._speaking_timer >= 4:
                        self._speaking_toggle = not self._speaking_toggle
                        self._speaking_timer = 0
                        
                    if self._speaking_toggle:
                        # Mouth closed state (using idle face but speaking pose if possible)
                        # The simple way is to alternate between speaking and idle completely.
                        img_state = AvatarState.IDLE
                    else:
                        img_state = AvatarState.SPEAKING
                        
                # Update character sprite
                current_img = self.images.get(img_state)
                if current_img:
                    self.avatar_canvas.itemconfig(self.char_ref, image=current_img)
            
            # --- Breathing / Hovering Animation ---
            # Make the character gently float up and down
            hover_y = 175 + 4 * math.sin(self._animation_phase * 0.5)
            self.avatar_canvas.coords(self.char_ref, self.width//2, hover_y)

            # Update Text
            self.status_label.config(text=self.status_text)
            if self.command_text:
                self.command_label.config(text=f'"{self.command_text}"')
            else:
                self.command_label.config(text="")
                
            # Change UI borders based on state
            border_color = {
                AvatarState.IDLE: "#7B2FBE",
                AvatarState.LISTENING: "#00E5FF",
                AvatarState.SPEAKING: "#E040FB",
                AvatarState.THINKING: "#FFD740",
                AvatarState.STARTUP: "#1DE9B6",
                AvatarState.ERROR: "#FF5252"
            }.get(self.state, "#7B2FBE")
            
            self.ui_frame.config(highlightbackground=border_color)
            self.status_label.config(fg=border_color)
            
            self.root.after(33, self._animate) # ~30 FPS
        except Exception:
            pass

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
    
    def _on_drag_motion(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")


def create_avatar():
    """Factory function to create and return an AvatarGUI instance"""
    avatar = AvatarGUI()
    return avatar

if __name__ == "__main__":
    print("🧙 Initializing VTuber Character Test...")
    avatar = AvatarGUI()
    avatar.start()
    
    try:
        time.sleep(2)
        print("Changing to IDLE")
        avatar.set_state(AvatarState.IDLE)
        avatar.set_status_text("Ready for commands")
        time.sleep(3)
        
        print("Changing to LISTENING")
        avatar.set_state(AvatarState.LISTENING)
        avatar.set_status_text("Listening...")
        time.sleep(3)
        
        print("Changing to THINKING")
        avatar.set_command_text("play some music")
        avatar.set_state(AvatarState.THINKING)
        avatar.set_status_text("Processing command...")
        time.sleep(3)
        
        print("Changing to SPEAKING")
        avatar.set_state(AvatarState.SPEAKING)
        avatar.set_status_text("Playing Cyberpunk 2077 radio via Spotify")
        time.sleep(5)
        
        print("Changing to IDLE")
        avatar.set_command_text("")
        avatar.set_state(AvatarState.IDLE)
        avatar.set_status_text("Ready")
        
        while avatar.running:
            time.sleep(1)
    except KeyboardInterrupt:
        avatar.stop()
