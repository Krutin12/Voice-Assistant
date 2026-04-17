import shutil
import os

BRAIN = r"C:\Users\krutin_12\.gemini\antigravity\brain\2ab83d9d-a013-49ec-b6ff-d21d4d5a0fde"
OUT = r"c:\Users\krutin_12\Documents\voice assistant\wizard\assets\character"

os.makedirs(OUT, exist_ok=True)

FILES = {
    "idle.png": os.path.join(BRAIN, "anime_idle_1774841776611.png"),
    "listening.png": os.path.join(BRAIN, "anime_listening_1774841792631.png"),
    "thinking.png": os.path.join(BRAIN, "anime_thinking_1774841830808.png"),
    "speaking.png": os.path.join(BRAIN, "anime_speaking_1774841851268.png"),
}

for out_name, src_path in FILES.items():
    if os.path.exists(src_path):
        out_path = os.path.join(OUT, out_name)
        shutil.copy2(src_path, out_path)
        print(f"Copied {src_path} -> {out_path}")
    else:
        print(f"Missing {src_path}")
