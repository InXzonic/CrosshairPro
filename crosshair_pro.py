import tkinter as tk
import json
import time
import threading
import sys
import win32api

# ================= FILE =================
PROFILE_FILE = "profiles.json"
TRANSPARENT_COLOR = "#010203"  # ultra-rare transparent key

# ================= DEFAULT SETTINGS =================
DEFAULTS = {
    "size": 18,
    "thickness": 2,
    "gap": 5,
    "r": 0,
    "g": 255,
    "b": 0,
    "mode": "cross",
    "recoil_strength": 2,
    "recoil_enabled": False
}

# ================= LOAD / SAVE =================
def load_settings():
    data = DEFAULTS.copy()
    try:
        with open(PROFILE_FILE, "r") as f:
            saved = json.load(f)
            if isinstance(saved, dict):
                data.update(saved)
    except:
        pass
    return data

def save_settings():
    with open(PROFILE_FILE, "w") as f:
        json.dump({
            "size": size.get(),
            "thickness": thickness.get(),
            "gap": gap.get(),
            "r": r.get(),
            "g": g.get(),
            "b": b.get(),
            "mode": mode.get(),
            "recoil_strength": recoil_strength.get(),
            "recoil_enabled": recoil_enabled
        }, f, indent=4)

settings = load_settings()

# ================= STATE =================
recoil_enabled = settings["recoil_enabled"]
recoil_offset = 0

# ================= OVERLAY =================
overlay = tk.Tk()
overlay.overrideredirect(True)
overlay.attributes("-topmost", True)
overlay.attributes("-transparentcolor", TRANSPARENT_COLOR)

sw = overlay.winfo_screenwidth()
sh = overlay.winfo_screenheight()
overlay.geometry(f"{sw}x{sh}+0+0")

canvas = tk.Canvas(
    overlay,
    bg=TRANSPARENT_COLOR,
    highlightthickness=0
)
canvas.pack(fill="both", expand=True)

# ================= VARIABLES =================
size = tk.IntVar(value=settings["size"])
thickness = tk.IntVar(value=settings["thickness"])
gap = tk.IntVar(value=settings["gap"])
r = tk.IntVar(value=settings["r"])
g = tk.IntVar(value=settings["g"])
b = tk.IntVar(value=settings["b"])
mode = tk.StringVar(value=settings["mode"])
recoil_strength = tk.IntVar(value=settings["recoil_strength"])

# ================= DRAW =================
def draw():
    canvas.delete("all")

    cx = sw // 2
    cy = (sh // 2) + recoil_offset

    rr, gg, bb = r.get(), g.get(), b.get()

    # safety: avoid transparent color collision
    if rr == 1 and gg == 2 and bb == 3:
        rr = 2

    color = f"#{rr:02x}{gg:02x}{bb:02x}"

    arm = size.get()
    gap_ = gap.get()
    thick = thickness.get()
    half = thick // 2
    rem = thick - half

    if mode.get() == "cross":
        canvas.create_rectangle(cx - gap_ - arm, cy - half, cx - gap_, cy + rem, fill=color, outline="")
        canvas.create_rectangle(cx + gap_, cy - half, cx + gap_ + arm, cy + rem, fill=color, outline="")
        canvas.create_rectangle(cx - half, cy - gap_ - arm, cx + rem, cy - gap_, fill=color, outline="")
        canvas.create_rectangle(cx - half, cy + gap_, cx + rem, cy + gap_ + arm, fill=color, outline="")

    elif mode.get() == "dot":
        d = max(2, thick)
        canvas.create_oval(cx - d, cy - d, cx + d, cy + d, fill=color, outline="")

    elif mode.get() == "circle":
        canvas.create_oval(cx - arm, cy - arm, cx + arm, cy + arm, outline=color, width=thick)

    overlay.after(16, draw)

# ================= RECOIL LOOP =================
def recoil_loop():
    global recoil_offset
    while True:
        if recoil_enabled and win32api.GetAsyncKeyState(0x01) < 0:
            recoil_offset = min(recoil_offset + recoil_strength.get(), 40)
        else:
            recoil_offset = max(recoil_offset - 3, 0)
        time.sleep(0.01)

threading.Thread(target=recoil_loop, daemon=True).start()

# ================= UI =================
ui = tk.Toplevel()
ui.title("Crosshair Pro")
ui.geometry("320x560")
ui.configure(bg="#0f0f0f")
ui.attributes("-topmost", True)

def slider(name, var, a, b):
    tk.Label(ui, text=name, bg="#0f0f0f", fg="white").pack()
    tk.Scale(ui, from_=a, to=b, orient="horizontal",
             variable=var, bg="#0f0f0f",
             fg="white", troughcolor="#222").pack(fill="x")

slider("Size", size, 3, 50)
slider("Thickness", thickness, 1, 10)
slider("Gap", gap, 0, 20)
slider("Red", r, 0, 255)
slider("Green", g, 0, 255)
slider("Blue", b, 0, 255)

tk.OptionMenu(ui, mode, "cross", "dot", "circle").pack(fill="x")

# ================= RECOIL TOGGLE =================
def toggle_recoil():
    global recoil_enabled, recoil_offset
    recoil_enabled = not recoil_enabled
    if not recoil_enabled:
        recoil_offset = 0
    recoil_btn.config(
        text="Disable Recoil Compensation" if recoil_enabled else "Enable Recoil Compensation"
    )

recoil_btn = tk.Button(ui, bg="#222", fg="white", command=toggle_recoil)
recoil_btn.pack(fill="x")
recoil_btn.config(
    text="Disable Recoil Compensation" if recoil_enabled else "Enable Recoil Compensation"
)

slider("Recoil Strength", recoil_strength, 1, 10)

# ================= SAVE & RESET =================
def reset_all():
    global recoil_enabled, recoil_offset
    recoil_enabled = False
    recoil_offset = 0

    size.set(DEFAULTS["size"])
    thickness.set(DEFAULTS["thickness"])
    gap.set(DEFAULTS["gap"])
    r.set(DEFAULTS["r"])
    g.set(DEFAULTS["g"])
    b.set(DEFAULTS["b"])
    mode.set(DEFAULTS["mode"])
    recoil_strength.set(DEFAULTS["recoil_strength"])

    recoil_btn.config(text="Enable Recoil Compensation")

tk.Button(ui, text="Save Settings", command=save_settings).pack(fill="x")
tk.Button(ui, text="Reset All", command=reset_all).pack(fill="x")

# ================= EXIT =================
def shutdown():
    overlay.destroy()
    ui.destroy()
    sys.exit()

ui.protocol("WM_DELETE_WINDOW", shutdown)

draw()
overlay.mainloop()
