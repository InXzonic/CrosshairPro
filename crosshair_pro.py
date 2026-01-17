import tkinter as tk
import json
import os
import threading
import time
import win32api

SETTINGS_FILE = "settings.json"


class CrosshairApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

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
            highlightthickness=0,
        )
        self.canvas.pack()

        self.center_x = 150
        self.center_y = 150

        # Settings variables
        self.size = tk.IntVar(value=20)
        self.thickness = tk.IntVar(value=2)
        self.gap = tk.IntVar(value=6)

        self.red = tk.IntVar(value=255)
        self.green = tk.IntVar(value=255)
        self.blue = tk.IntVar(value=255)

        self.recoil_enabled = False
        self.recoil_strength = tk.IntVar(value=2)

        self.running = True

        self.load_settings()
        self.create_ui()
        self.update_crosshair()

        self.recoil_thread = threading.Thread(target=self.recoil_loop, daemon=True)
        self.recoil_thread.start()

        self.root.mainloop()

    # ---------------- UI ----------------

    def create_ui(self):
        self.ui = tk.Toplevel()
        self.ui.title("Crosshair Pro")
        self.ui.protocol("WM_DELETE_WINDOW", self.exit_app)

        try:
            self.ui.iconbitmap("crosshair.ico")
        except:
            pass

        self.slider(self.ui, "Size", self.size, 5, 60)
        self.slider(self.ui, "Thickness", self.thickness, 1, 10)
        self.slider(self.ui, "Center Gap", self.gap, 0, 30)

        tk.Label(self.ui, text="Color (RGB)").pack()
        self.slider(self.ui, "Red", self.red, 0, 255)
        self.slider(self.ui, "Green", self.green, 0, 255)
        self.slider(self.ui, "Blue", self.blue, 0, 255)

        tk.Label(self.ui, text="Recoil Strength").pack()
        tk.Scale(
            self.ui,
            from_=1,
            to=10,
            orient="horizontal",
            variable=self.recoil_strength,
        ).pack(fill="x")

        self.recoil_button = tk.Button(
            self.ui,
            text="Enable Recoil Compensation",
            command=self.toggle_recoil,
        )
        self.recoil_button.pack(pady=5)

        tk.Button(self.ui, text="Save Settings", command=self.save_settings).pack(fill="x")
        tk.Button(self.ui, text="Reset All", command=self.reset_settings).pack(fill="x")

    def slider(self, parent, text, var, minv, maxv):
        tk.Label(parent, text=text).pack()
        tk.Scale(
            parent,
            from_=minv,
            to=maxv,
            orient="horizontal",
            variable=var,
            command=lambda e: self.update_crosshair(),
        ).pack(fill="x")

    # ---------------- Crosshair ----------------

    def update_crosshair(self):
        self.canvas.delete("all")

        size = self.size.get()
        gap = self.gap.get()
        thick = self.thickness.get()

        color = f"#{self.red.get():02x}{self.green.get():02x}{self.blue.get():02x}"

        cx = self.center_x
        cy = self.center_y

        # Left
        self.canvas.create_line(
            cx - gap - size,
            cy,
            cx - gap,
            cy,
            fill=color,
            width=thick,
        )
        # Right
        self.canvas.create_line(
            cx + gap,
            cy,
            cx + gap + size,
            cy,
            fill=color,
            width=thick,
        )
        # Top
        self.canvas.create_line(
            cx,
            cy - gap - size,
            cx,
            cy - gap,
            fill=color,
            width=thick,
        )
        # Bottom
        self.canvas.create_line(
            cx,
            cy + gap,
            cx,
            cy + gap + size,
            fill=color,
            width=thick,
        )

        self.crosshair.geometry("+{}+{}".format(
            win32api.GetSystemMetrics(0)//2 - 150,
            win32api.GetSystemMetrics(1)//2 - 150,
        ))

        self.root.after(10, self.update_crosshair)

    # ---------------- Recoil ----------------

    def toggle_recoil(self):
        self.recoil_enabled = not self.recoil_enabled
        if self.recoil_enabled:
            self.recoil_button.config(text="Disable Recoil Compensation")
        else:
            self.recoil_button.config(text="Enable Recoil Compensation")

    def recoil_loop(self):
        while self.running:
            if self.recoil_enabled and win32api.GetAsyncKeyState(0x01):
                win32api.mouse_event(
                    0x0001,
                    0,
                    self.recoil_strength.get(),
                    0,
                    0,
                )
            time.sleep(0.01)

    # ---------------- Settings ----------------

    def save_settings(self):
        data = {
            "size": self.size.get(),
            "thickness": self.thickness.get(),
            "gap": self.gap.get(),
            "red": self.red.get(),
            "green": self.green.get(),
            "blue": self.blue.get(),
            "recoil_strength": self.recoil_strength.get(),
            "recoil_enabled": self.recoil_enabled,
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)

        self.size.set(data.get("size", 20))
        self.thickness.set(data.get("thickness", 2))
        self.gap.set(data.get("gap", 6))
        self.red.set(data.get("red", 255))
        self.green.set(data.get("green", 255))
        self.blue.set(data.get("blue", 255))
        self.recoil_strength.set(data.get("recoil_strength", 2))
        self.recoil_enabled = data.get("recoil_enabled", False)

    def reset_settings(self):
        self.size.set(20)
        self.thickness.set(2)
        self.gap.set(6)
        self.red.set(255)
        self.green.set(255)
        self.blue.set(255)
        self.recoil_strength.set(2)
        self.recoil_enabled = False
        self.recoil_button.config(text="Enable Recoil Compensation")
        self.save_settings()

    # ---------------- Exit ----------------

    def exit_app(self):
        self.running = False
        self.root.destroy()
        os._exit(0)


if __name__ == "__main__":
    CrosshairApp()
