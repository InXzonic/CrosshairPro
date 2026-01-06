import tkinter as tk
import json
import time
import threading
import sys
import win32api

# ================= FILE =================
PROFILE_FILE = "profiles.json"

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
    try:
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    except:
        return DEFAULTS.copy()

def save_settings():
    data = {
        "size": size.get(),
        "thickness": thickness.get(),
        "gap": gap.get(),
        "r": r.get(),
        "g": g.get(),
        "b": b.get(),
        "mode": mode.get(),
        "recoil_strength": recoil_strength.get(),
        "recoil_enabled": recoil_enabled
    }
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=4)

settings = load_settings()

# ================= STATE =================
recoil_enabled = settings.get("recoil_enabled", False)
recoil_offset = 0

# ================= OVERLAY =================
overlay = tk.Tk()
overlay.overrideredirect(True)
overlay.attributes("-topmost", True)
overlay.attributes("-transparentcolor", "black")

sw = overlay.winfo_screenwidth()
sh = overlay.winfo_screenheight()
overlay.geometry(f"{sw}x{sh}+0+0")

canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)

# ================= VARIABLES =================
size = tk.IntVar(value=settings.get("size", DEFAULTS["size"]))
thickness = tk.IntVar(value=settings.get("thickness", DEFAULTS["thickness"]))
gap = tk.IntVar(value=settings.get("gap", DEFAULTS["gap"]))
r = tk.IntVar(value=settings.get("r", DEFAULTS["r"]))
g = tk.IntVar(value=settings.get("g", DEFAULTS["g"]))
b = tk.IntVar(value=settings.get("b", DEFAULTS["b"]))
mode = tk.StringVar(value=settings.get("mode", DEFAULTS["mode"]))
recoil_strength = tk.IntVar(value=settings.get("recoil_strength", DEFAULTS["recoil_strength"]))

# ================= DRAW =================
def draw():
    canvas.delete("all")

    cx = sw // 2
    cy = (sh // 2) + recoil_offset
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
ui.geometry("320x550")
ui.configure(bg="#0f0f0f")
ui.attributes("-topmost", True)

def slider(text, var, f, t):
    tk.Label(ui, text=text, bg="#0f0f0f", fg="white").pack()
    tk.Scale(
        ui, from_=f, to=t, orient="horizontal",
        variable=var, bg="#0f0f0f",
        fg="white", troughcolor="#222"
    ).pack(fill="x")

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
    update_recoil_button()

def update_recoil_button():
    recoil_button.config(
        text="Disable Recoil Compensation" if recoil_enabled
        else "Enable Recoil Compensation"
    )

recoil_button = tk.Button(ui, bg="#222", fg="white", command=toggle_recoil)
recoil_button.pack(fill="x")
update_recoil_button()

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
    update_recoil_button()

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
