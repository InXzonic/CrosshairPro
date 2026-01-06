import tkinter as tk
import json
import time
import threading
import math
import keyboard
import psutil
import win32gui
import win32con
import pystray
from PIL import Image, ImageDraw

# ===================== FILE =====================
PROFILE_FILE = "profiles.json"

# ===================== STATE =====================
enabled = True
recoil_enabled = False
pulse_enabled = False
recoil_offset = 0
pulse_phase = 0

# ===================== LOAD PROFILES =====================
def load_profiles():
    try:
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

profiles = load_profiles()

# ===================== OVERLAY WINDOW =====================
overlay = tk.Tk()
overlay.overrideredirect(True)
overlay.attributes("-topmost", True)
overlay.attributes("-transparentcolor", "black")

screen_w = overlay.winfo_screenwidth()
screen_h = overlay.winfo_screenheight()
overlay.geometry(f"{screen_w}x{screen_h}+0+0")

canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)

hwnd = win32gui.GetForegroundWindow()
win32gui.SetWindowLong(
    hwnd,
    win32con.GWL_EXSTYLE,
    win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    | win32con.WS_EX_LAYERED
    | win32con.WS_EX_TRANSPARENT
)

# ===================== VARIABLES =====================
size = tk.IntVar(value=18)
thickness = tk.IntVar(value=2)
gap = tk.IntVar(value=5)
red = tk.IntVar(value=0)
green = tk.IntVar(value=255)
blue = tk.IntVar(value=0)
mode = tk.StringVar(value="cross")

# ===================== DRAW CROSSHAIR =====================
def draw():
    global recoil_offset, pulse_phase
    canvas.delete("all")

    if not enabled:
        overlay.after(16, draw)
        return

    cx = screen_w // 2
    cy = screen_h // 2 + recoil_offset
    color = f"#{red.get():02x}{green.get():02x}{blue.get():02x}"

    pulse_size = 0
    if pulse_enabled:
        pulse_phase += 0.08
        pulse_size = int(math.sin(pulse_phase) * 2)

    s = size.get() + pulse_size
    t = thickness.get()
    g = gap.get()

    if mode.get() == "cross":
        canvas.create_rectangle(cx-g-s, cy-t//2, cx-g, cy+t//2, fill=color, outline="")
        canvas.create_rectangle(cx+g, cy-t//2, cx+g+s, cy+t//2, fill=color, outline="")
        canvas.create_rectangle(cx-t//2, cy-g-s, cx+t//2, cy-g, fill=color, outline="")
        canvas.create_rectangle(cx-t//2, cy+g, cx+t//2, cy+g+s, fill=color, outline="")

    elif mode.get() == "dot":
        canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill=color, outline="")

    elif mode.get() == "circle":
        canvas.create_oval(cx-s, cy-s, cx+s, cy+s, outline=color, width=t)

    overlay.after(16, draw)

# ===================== RECOIL LOOP =====================
def recoil_loop():
    global recoil_offset
    while True:
        if recoil_enabled and keyboard.is_pressed("left mouse"):
            recoil_offset += 1
        else:
            recoil_offset = max(0, recoil_offset - 1)
        time.sleep(0.01)

threading.Thread(target=recoil_loop, daemon=True).start()

# ===================== GAME DETECTOR =====================
def game_detector():
    last = ""
    while True:
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32gui.GetWindowThreadProcessId(hwnd)
            name = psutil.Process(pid).name().lower()

            if name != last:
                if "cs2" in name and "cs2" in profiles:
                    apply_profile("cs2")
                if "valorant" in name and "valorant" in profiles:
                    apply_profile("valorant")
                last = name
        except:
            pass
        time.sleep(1)

def apply_profile(name):
    p = profiles.get(name)
    if not p:
        return
    size.set(p["size"])
    thickness.set(p["thickness"])
    gap.set(p["gap"])
    red.set(p["red"])
    green.set(p["green"])
    blue.set(p["blue"])
    mode.set(p["mode"])

threading.Thread(target=game_detector, daemon=True).start()

# ===================== UI WINDOW =====================
ui = tk.Toplevel()
ui.title("Crosshair Pro")
ui.geometry("320x620")
ui.configure(bg="#0f0f0f")
ui.attributes("-topmost", True)

def slider(text, var, start, end):
    tk.Label(ui, text=text, bg="#0f0f0f", fg="white").pack()
    tk.Scale(ui, from_=start, to=end, orient="horizontal",
             variable=var, bg="#0f0f0f", fg="white",
             troughcolor="#222").pack(fill="x")

slider("Size", size, 3, 50)
slider("Thickness", thickness, 1, 10)
slider("Gap", gap, 0, 20)
slider("Red", red, 0, 255)
slider("Green", green, 0, 255)
slider("Blue", blue, 0, 255)

tk.OptionMenu(ui, mode, "cross", "dot", "circle").pack(fill="x")

def toggle_recoil():
    global recoil_enabled
    recoil_enabled = not recoil_enabled

def toggle_pulse():
    global pulse_enabled
    pulse_enabled = not pulse_enabled

tk.Checkbutton(ui, text="Recoil Compensation",
               command=toggle_recoil,
               bg="#0f0f0f", fg="white").pack(fill="x")

tk.Checkbutton(ui, text="Pulse Animation",
               command=toggle_pulse,
               bg="#0f0f0f", fg="white").pack(fill="x")

# ===================== SAVE PROFILES =====================
def save_profile(name):
    profiles[name] = {
        "size": size.get(),
        "thickness": thickness.get(),
        "gap": gap.get(),
        "red": red.get(),
        "green": green.get(),
        "blue": blue.get(),
        "mode": mode.get()
    }
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

tk.Button(ui, text="Save CS2 Profile",
          command=lambda: save_profile("cs2")).pack(fill="x")

tk.Button(ui, text="Save Valorant Profile",
          command=lambda: save_profile("valorant")).pack(fill="x")

# ===================== HOTKEY =====================
def toggle_crosshair():
    global enabled
    enabled = not enabled

keyboard.add_hotkey("ctrl+alt+x", toggle_crosshair)

# ===================== SYSTEM TRAY =====================
def tray_icon():
    img = Image.new("RGB", (64, 64), "black")
    draw_img = ImageDraw.Draw(img)
    draw_img.line((32, 0, 32, 64), fill="green", width=3)
    draw_img.line((0, 32, 64, 32), fill="green", width=3)

    def quit_app(icon, item):
        icon.stop()
        overlay.destroy()

    menu = pystray.Menu(pystray.MenuItem("Quit", quit_app))
    pystray.Icon("CrosshairPro", img, "Crosshair Pro", menu).run()

threading.Thread(target=tray_icon, daemon=True).start()

# ===================== START =====================
draw()
overlay.mainloop()
