import tkinter as tk
import json
import os
import threading
import time
import win32api

SETTINGS_FILE = "settings.json"

BG = "#0b0e14"
BOX = "#141823"
TEXT = "#dcdcdc"
ACCENT = "#00bcd4"
BORDER = "#2a2f3a"


class CrosshairApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        # Crosshair overlay
        self.crosshair = tk.Toplevel()
        self.crosshair.overrideredirect(True)
        self.crosshair.attributes("-topmost", True)
        self.crosshair.attributes("-transparentcolor", "magenta")
        self.crosshair.configure(bg="magenta")

        self.canvas = tk.Canvas(
            self.crosshair,
            width=300,
            height=300,
            bg="magenta",
            highlightthickness=0
        )
        self.canvas.pack()

        self.center_x = 150
        self.base_center_y = 150
        self.recoil_offset = 0

        # Variables
        self.size = tk.IntVar(value=20)
        self.thickness = tk.IntVar(value=2)
        self.gap = tk.IntVar(value=6)

        self.red = tk.IntVar(value=255)
        self.green = tk.IntVar(value=255)
        self.blue = tk.IntVar(value=255)

        self.recoil_strength = tk.IntVar(value=2)
        self.recoil_enabled = False
        self.running = True

        self.load_settings()
        self.create_ui()
        self.update_crosshair()

        threading.Thread(target=self.recoil_loop, daemon=True).start()
        self.root.mainloop()

    # ---------------- UI ----------------

    def create_ui(self):
        self.ui = tk.Toplevel()
        self.ui.title("Crosshair Pro")
        self.ui.configure(bg=BG)
        self.ui.resizable(False, False)
        self.ui.protocol("WM_DELETE_WINDOW", self.exit_app)

        try:
            self.ui.iconbitmap("crosshair.ico")
        except:
            pass

        def box(title):
            outer = tk.Frame(
                self.ui, bg=BORDER, padx=1, pady=1
            )
            inner = tk.Frame(
                outer, bg=BOX, padx=10, pady=8
            )
            outer.pack(fill="x", padx=10, pady=6)
            inner.pack(fill="x")

            tk.Label(
                inner, text=title,
                fg=ACCENT, bg=BOX,
                font=("Segoe UI", 9, "bold")
            ).pack(anchor="w", pady=(0, 6))

            return inner

        def slider(parent, text, var, a, b):
            tk.Label(parent, text=text, fg=TEXT, bg=BOX).pack(anchor="w")
            tk.Scale(
                parent,
                from_=a, to=b,
                orient="horizontal",
                variable=var,
                bg=BOX,
                fg=TEXT,
                troughcolor=BORDER,
                highlightthickness=0,
                length=220
            ).pack(fill="x")

        # -------- Boxes --------

        b1 = box("CROSSHAIR")
        slider(b1, "Size", self.size, 5, 60)
        slider(b1, "Thickness", self.thickness, 1, 10)
        slider(b1, "Center Gap", self.gap, 0, 30)

        b2 = box("COLOR (RGB)")
        slider(b2, "Red", self.red, 0, 255)
        slider(b2, "Green", self.green, 0, 255)
        slider(b2, "Blue", self.blue, 0, 255)

        b3 = box("RECOIL")
        slider(b3, "Strength", self.recoil_strength, 1, 10)

        self.recoil_btn = tk.Button(
            b3,
            text="ENABLE RECOIL",
            bg=BOX,
            fg=ACCENT,
            activebackground=ACCENT,
            activeforeground="#000",
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            command=self.toggle_recoil
        )
        self.recoil_btn.pack(fill="x", pady=6)

        b4 = box("SETTINGS")
        tk.Button(
            b4,
            text="SAVE SETTINGS",
            bg=BOX,
            fg=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            command=self.save_settings
        ).pack(fill="x", pady=3)

        tk.Button(
            b4,
            text="RESET ALL",
            bg=BOX,
            fg="#ff6b6b",
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            command=self.reset_settings
        ).pack(fill="x")

    # ---------------- Crosshair ----------------

    def update_crosshair(self):
        self.canvas.delete("all")

        cx = self.center_x
        cy = self.base_center_y + int(self.recoil_offset)

        size = self.size.get()
        gap = self.gap.get()
        thick = self.thickness.get()
        color = f"#{self.red.get():02x}{self.green.get():02x}{self.blue.get():02x}"

        self.canvas.create_line(cx-gap-size, cy, cx-gap, cy, fill=color, width=thick)
        self.canvas.create_line(cx+gap, cy, cx+gap+size, cy, fill=color, width=thick)
        self.canvas.create_line(cx, cy-gap-size, cx, cy-gap, fill=color, width=thick)
        self.canvas.create_line(cx, cy+gap, cx, cy+gap+size, fill=color, width=thick)

        self.crosshair.geometry(
            "+{}+{}".format(
                win32api.GetSystemMetrics(0)//2 - 150,
                win32api.GetSystemMetrics(1)//2 - 150
            )
        )

        self.root.after(10, self.update_crosshair)

    # ---------------- Recoil ----------------

    def toggle_recoil(self):
        self.recoil_enabled = not self.recoil_enabled
        self.recoil_btn.config(
            text="DISABLE RECOIL" if self.recoil_enabled else "ENABLE RECOIL",
            bg=ACCENT if self.recoil_enabled else BOX,
            fg="#000" if self.recoil_enabled else ACCENT
        )

    def recoil_loop(self):
        while self.running:
            if self.recoil_enabled and win32api.GetAsyncKeyState(0x01):
                self.recoil_offset += self.recoil_strength.get() * 0.2
            else:
                self.recoil_offset *= 0.85
            time.sleep(0.01)

    # ---------------- Settings ----------------

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump({
                "size": self.size.get(),
                "thickness": self.thickness.get(),
                "gap": self.gap.get(),
                "red": self.red.get(),
                "green": self.green.get(),
                "blue": self.blue.get(),
                "recoil_strength": self.recoil_strength.get(),
                "recoil_enabled": self.recoil_enabled
            }, f)

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        with open(SETTINGS_FILE) as f:
            d = json.load(f)

        self.size.set(d.get("size", 20))
        self.thickness.set(d.get("thickness", 2))
        self.gap.set(d.get("gap", 6))
        self.red.set(d.get("red", 255))
        self.green.set(d.get("green", 255))
        self.blue.set(d.get("blue", 255))
        self.recoil_strength.set(d.get("recoil_strength", 2))
        self.recoil_enabled = d.get("recoil_enabled", False)

    def reset_settings(self):
        self.size.set(20)
        self.thickness.set(2)
        self.gap.set(6)
        self.red.set(255)
        self.green.set(255)
        self.blue.set(255)
        self.recoil_strength.set(2)
        self.recoil_enabled = False
        self.recoil_offset = 0
        self.recoil_btn.config(text="ENABLE RECOIL", bg=BOX, fg=ACCENT)
        self.save_settings()

    # ---------------- Exit ----------------

    def exit_app(self):
        self.running = False
        self.root.destroy()
        os._exit(0)


if __name__ == "__main__":
    CrosshairApp()
