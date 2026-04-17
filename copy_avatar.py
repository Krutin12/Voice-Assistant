"""Quick script to copy avatar image to assets folder"""
import shutil, os
src = r'C:\Users\krutin_12\.gemini\antigravity\brain\a86ac9eb-01c9-4255-a83d-e02f63c7a36c\dashboard_assistant_character_1774245190605.png'
dst = os.path.join(os.path.dirname(__file__), 'wizard', 'assets', 'avatar.png')
os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copy2(src, dst)
print(f"Copied avatar to: {dst}")
print(f"File size: {os.path.getsize(dst)} bytes")
