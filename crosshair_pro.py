import tkinter as tk
import json, time, threading
import keyboard, psutil
import win32gui, win32con, win32api
import pystray
from PIL import Image, ImageDraw

# ================= FILE =================
PROFILE_FILE = "profiles.json"

# ================= STATE =================
enabled = True
recoil = False
recoil_offset = 0

# ================= LOAD PROFILES =================
def load_profiles():
    try:
        with open(PROFILE_FILE) as f:
            return json.load(f)
    except:
        return {}

profiles = load_profiles()

# ================= OVERLAY =================
overlay = tk.Tk()
overlay.overrideredirect(True)
overlay.attributes("-topmost", True)
overlay.attributes("-transparentcolor", "black")

sw, sh = overlay.winfo_screenwidth(), overlay.winfo_screenheight()
overlay.geometry(f"{sw}x{sh}+0+0")

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

# ================= VARIABLES =================
size = tk.IntVar(value=18)
thickness = tk.IntVar(value=2)
gap = tk.IntVar(value=5)
r = tk.IntVar(value=0)
g = tk.IntVar(value=255)
b = tk.IntVar(value=0)
mode = tk.StringVar(value="cross")
recoil_strength = tk.IntVar(value=2)

# ================= DRAW =================
def draw():
    canvas.delete("all")

    if not enabled:
        overlay.after(16, draw)
        return

    cx, cy = sw // 2, sh // 2 + recoil_offset
    color = f"#{r.get():02x}{g.get():02x}{b.get():02x}"

    s = size.get()
    t = thickness.get()
    gapp = gap.get()

    if mode.get() == "cross":
        canvas.create_rectangle(cx-gapp-s, cy-t//2, cx-gapp, cy+t//2, fill=color, outline="")
        canvas.create_rectangle(cx+gapp, cy-t//2, cx+gapp+s, cy+t//2, fill=color, outline="")
        canvas.create_rectangle(cx-t//2, cy-gapp-s, cx+t//2, cy-gapp, fill=color, outline="")
        canvas.create_rectangle(cx-t//2, cy+gapp, cx+t//2, cy+gapp+s, fill=color, outline="")

    elif mode.get() == "dot":
        canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill=color, outline="")

    elif mode.get() == "circle":
        canvas.create_oval(cx-s, cy-s, cx+s, cy+s, outline=color, width=t)

    overlay.after(16, draw)

# ================= RECOIL (FIXED & WORKING) =================
def recoil_loop():
    global recoil_offset
    while True:
        if recoil:
            if win32api.GetAsyncKeyState(0x01) < 0:  # Left Mouse Button
                recoil_offset = min(
                    recoil_offset + recoil_strength.get(),
                    40
                )
            else:
                recoil_offset = max(recoil_offset - 3, 0)
        time.sleep(0.01)

threading.Thread(target=recoil_loop, daemon=True).start()

# ================= GAME AUTO PROFILE =================
def game_detector():
    last = None
    while True:
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32gui.GetWindowThreadProcessId(hwnd)
            name = psutil.Process(pid).name().lower()

            if name != last:
                if "cs2" in name:
                    load_profile("cs2")
                elif "valorant" in name:
                    load_profile("valorant")
                last = name
        except:
            pass
        time.sleep(1)

def load_profile(name):
    p = profiles.get(name)
    if p:
        size.set(p["size"])
        thickness.set(p["thickness"])
        gap.set(p["gap"])
        r.set(p["r"]); g.set(p["g"]); b.set(p["b"])
        mode.set(p["mode"])

threading.Thread(target=game_detector, daemon=True).start()

# ================= UI =================
ui = tk.Toplevel()
ui.title("Crosshair Pro")
ui.geometry("320x600")
ui.configure(bg="#0f0f0f")
ui.attributes("-topmost", True)

def slider(text, var, f, t):
    tk.Label(ui, text=text, bg="#0f0f0f", fg="white").pack()
    tk.Scale(ui, from_=f, to=t, orient="horizontal",
             variable=var, bg="#0f0f0f",
             fg="white", troughcolor="#222").pack(fill="x")

slider("Size", size, 3, 50)
slider("Thickness", thickness, 1, 10)
slider("Gap", gap, 0, 20)

slider("Red", r, 0, 255)
slider("Green", g, 0, 255)
slider("Blue", b, 0, 255)

tk.OptionMenu(ui, mode, "cross", "dot", "circle").pack(fill="x")

tk.Checkbutton(
    ui,
    text="Enable Recoil Compensation",
    bg="#0f0f0f",
    fg="white",
    command=lambda: globals().__setitem__("recoil", not recoil)
).pack(fill="x")

slider("Recoil Strength", recoil_strength, 1, 10)

# ================= SAVE PROFILES =================
def save_profile(name):
    profiles[name] = {
        "size": size.get(),
        "thickness": thickness.get(),
        "gap": gap.get(),
        "r": r.get(),
        "g": g.get(),
        "b": b.get(),
        "mode": mode.get()
    }
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

tk.Button(ui, text="Save as CS2", command=lambda: save_profile("cs2")).pack(fill="x")
tk.Button(ui, text="Save as Valorant", command=lambda: save_profile("valorant")).pack(fill="x")

# ================= HOTKEY =================
keyboard.add_hotkey("ctrl+alt+x", lambda: globals().__setitem__("enabled", not enabled))

# ================= TRAY =================
def tray():
    img = Image.new("RGB", (64, 64), "black")
    d = ImageDraw.Draw(img)
    d.line((32, 0, 32, 64), fill="green", width=3)
    d.line((0, 32, 64, 32), fill="green", width=3)

    def quit_app(icon, item):
        icon.stop()
        overlay.destroy()

    pystray.Icon(
        "CrosshairPro",
        img,
        "Crosshair Pro",
        pystray.Menu(pystray.MenuItem("Quit", quit_app))
    ).run()

threading.Thread(target=tray, daemon=True).start()

draw()
overlay.mainloop()
