7#!/usr/bin/env python3
"""Process sprite images: remove green screen background using numpy for speed."""
from PIL import Image
import numpy as np
import os

BRAIN = r"C:\Users\krutin_12\.gemini\antigravity\brain\2ab83d9d-a013-49ec-b6ff-d21d4d5a0fde"
OUT = os.path.dirname(os.path.abspath(__file__))

FILES = {
    "idle.png": os.path.join(BRAIN, "anime_idle_1774841776611.png"),
    "listening.png": os.path.join(BRAIN, "anime_listening_1774841792631.png"),
    "thinking.png": os.path.join(BRAIN, "anime_thinking_1774841830808.png"),
    "speaking.png": os.path.join(BRAIN, "anime_speaking_1774841851268.png"),
}

TARGET_SIZE = (400, 400)  # Resize to reasonable desktop mascot size

for out_name, src_path in FILES.items():
    print(f"Processing {out_name}...")
    img = Image.open(src_path).convert("RGBA")
    arr = np.array(img)
    
    r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]
    
    # Green screen mask: high green, low red and blue
    green_mask = (g > 150) & (r < (g - 50)) & (b < (g - 50))
    
    # Set alpha to 0 where green
    arr[green_mask, 3] = 0
    
    result = Image.fromarray(arr)
    result = result.resize(TARGET_SIZE, Image.LANCZOS)
    
    out_path = os.path.join(OUT, out_name)
    result.save(out_path, "PNG")
    print(f"  -> Saved {out_path} ({os.path.getsize(out_path)} bytes)")

print("All done!")
