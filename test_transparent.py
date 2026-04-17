import tkinter as tk
from PIL import Image, ImageTk
import os

root = tk.Tk()
# Use green as transparent color
root.attributes('-transparentcolor', '#00ff00')
root.overrideredirect(True)
root.attributes('-topmost', True)
root.geometry("400x400+800+400")

# Set window background to green
root.configure(bg='#00ff00')

canvas = tk.Canvas(root, width=400, height=400, bg='#00ff00', highlightthickness=0)
canvas.pack()

IMG_PATH = r"C:\Users\krutin_12\.gemini\antigravity\brain\2ab83d9d-a013-49ec-b6ff-d21d4d5a0fde\anime_idle_1774841776611.png"

try:
    img = Image.open(IMG_PATH)
    # Resize slightly
    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    canvas.create_image(200, 200, image=photo)
except Exception as e:
    canvas.create_text(200, 200, text=str(e), fill="black")

def close(e):
    root.destroy()
root.bind("<Button-1>", close)

root.after(3000, root.destroy) # close automatically after 3 sec
root.mainloop()
