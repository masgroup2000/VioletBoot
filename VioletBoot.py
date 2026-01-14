import os
import sys
import subprocess
import json
import hashlib
import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

### THEME ###
COLOR_BG = "#13091F"
COLOR_CARD = "#2A1845"
COLOR_ACCENT = "#8B2CF5"
COLOR_HOVER = "#A65DFF"
COLOR_TEXT = "#E0D9F6"
COLOR_DANGER = "#FF4444"
COLOR_SUCCESS = "#00E676"

def setup_theme():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")

### SYSTEM UTILS ###
def force_sync(file_obj=None):
    if file_obj:
        file_obj.flush()
        os.fsync(file_obj.fileno())
    os.sync()

### DRIVE MANAGER ###
class DriveManager:

    @staticmethod
    def get_usb_drives():
        drives = []
        try:
            cmd = ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,TRAN,MODEL"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return []

            data = json.loads(result.stdout)
            for dev in data.get("blockdevices", []):
                if dev.get("tran") == "usb" and dev.get("type") == "disk":
                    label = f"{dev.get('model','USB')} ({dev.get('size')}) - /dev/{dev['name']}"
                    drives.append({
                        "label": label,
                        "path": f"/dev/{dev['name']}"
                    })
        except:
            pass

        return drives

    @staticmethod
    def unmount_drive(device):
        try:
            result = subprocess.run(
                ["lsblk", "-nlo", "MOUNTPOINT", device],
                capture_output=True,
                text=True
            )
            for mount in result.stdout.splitlines():
                if mount.strip():
                    subprocess.run(["umount", "-l", mount.strip()])
            return True
        except:
            return False

### ISO WRITER ###
CHUNK_SIZE = 16 * 1024 * 1024  

def write_iso(
    iso_path,
    device_path,
    verify=True,
    progress_cb=None,
    status_cb=None
):
    DriveManager.unmount_drive(device_path)

    size = os.path.getsize(iso_path)
    written = 0
    src_hash = hashlib.sha256()

    if status_cb:
        status_cb("Writing image...")

    with open(iso_path, "rb") as src, open(device_path, "wb") as dst:
        while True:
            data = src.read(CHUNK_SIZE)
            if not data:
                break

            if verify:
                src_hash.update(data)

            dst.write(data)
            written += len(data)

            if progress_cb:
                progress_cb(written / size)

        force_sync(dst)

    if not verify:
        return True

    if status_cb:
        status_cb("Verifying integrity...")

    dst_hash = hashlib.sha256()
    read = 0

    with open(device_path, "rb") as dev:
        while read < size:
            data = dev.read(min(CHUNK_SIZE, size - read))
            if not data:
                break
            dst_hash.update(data)
            read += len(data)

            if progress_cb:
                progress_cb(read / size)

    return src_hash.hexdigest() == dst_hash.hexdigest()

### UI ###
class VioletBootApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        if os.geteuid() != 0:
            messagebox.showerror("Permission Error", "Run as root (sudo).")
            sys.exit(1)

        setup_theme()

        self.title("VioletBoot | masgroup")        
        self.geometry("500x700")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        self.iso = None
        self.drives = {}
        self.verify = tk.BooleanVar(value=True)

        self.build_ui()
        self.scan_drives()

    def build_ui(self):
        # Title
        ctk.CTkLabel(
            self, 
            text="VIOLETBOOT", 
            font=("Roboto", 28, "bold"), 
            text_color=COLOR_ACCENT
        ).pack(pady=25)

        # Main card container
        card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=15)
        card.pack(padx=30, pady=10, fill="both", expand=True)

        # USB Drive selection
        ctk.CTkLabel(
            card, 
            text="Select USB Drive", 
            font=("Roboto", 12), 
            text_color=COLOR_TEXT
        ).pack(pady=(20, 5))

        self.combo = ctk.CTkComboBox(
            card, 
            values=["Scanning..."], 
            width=420, 
            height=40,
            font=("Roboto", 14),
            dropdown_font=("Roboto", 12),
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_HOVER
        )
        self.combo.pack(pady=5)

        # Refresh button
        ctk.CTkButton(
            card, 
            text="🔄 Refresh Drives", 
            command=self.scan_drives,
            width=120,
            height=30,
            fg_color=COLOR_BG,
            hover_color=COLOR_CARD,
            font=("Roboto", 11)
        ).pack(pady=8)

        # ISO selection
        ctk.CTkLabel(
            card, 
            text="Select ISO File", 
            font=("Roboto", 12), 
            text_color=COLOR_TEXT
        ).pack(pady=(15, 5))

        ctk.CTkButton(
            card, 
            text="📁 Browse ISO", 
            command=self.pick_iso,
            height=38,
            width=200,
            font=("Roboto", 13),
            fg_color=COLOR_BG,
            hover_color=COLOR_ACCENT
        ).pack(pady=5)

        self.iso_label = ctk.CTkLabel(
            card, 
            text="No ISO selected", 
            text_color="gray60",
            font=("Roboto", 11)
        )
        self.iso_label.pack(pady=5)

        # Verify 
        ctk.CTkCheckBox(
            card, 
            text="Verify after write (recommended)", 
            variable=self.verify,
            font=("Roboto", 12),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_HOVER
        ).pack(pady=15)

        # Progress
        self.progress = ctk.CTkProgressBar(
            card,
            height=20,
            progress_color=COLOR_ACCENT
        )
        self.progress.pack(padx=30, pady=15, fill="x")
        self.progress.set(0)

        # Status
        self.status = ctk.CTkLabel(
            card, 
            text="Ready", 
            text_color="gray60",
            font=("Roboto", 12)
        )
        self.status.pack(pady=5)

        # Flash
        self.btn = ctk.CTkButton(
            card, 
            text="⚡ FLASH USB", 
            height=55,
            font=("Roboto", 18, "bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_HOVER,
            command=self.start
        )
        self.btn.pack(pady=20, padx=30, fill="x")

    def scan_drives(self):
        drives = DriveManager.get_usb_drives()
        self.drives = {d["label"]: d["path"] for d in drives}

        if not drives:
            self.combo.configure(values=["No USB Found"])
            self.combo.set("No USB Found")
        else:
            self.combo.configure(values=list(self.drives.keys()))
            self.combo.set(list(self.drives.keys())[0])

    def pick_iso(self):
        path = filedialog.askopenfilename(filetypes=[("ISO Images", "*.iso *.img")])
        if path:
            self.iso = path
            filename = os.path.basename(path)
            # long file name fix
            if len(filename) > 40:
                filename = filename[:37] + "..."
            self.iso_label.configure(text=filename, text_color=COLOR_TEXT)

    def start(self):
        device = self.drives.get(self.combo.get())
        if not self.iso or not device:
            messagebox.showerror("Error", "Please select both ISO and USB drive")
            return

        if not messagebox.askyesno("⚠️ Confirm", f"This will ERASE all data on:\n{device}\n\nContinue?"):
            return

        self.btn.configure(state="disabled", text="⏳ Flashing...")
        self.progress.set(0)
        threading.Thread(target=self.run_flash, args=(device,), daemon=True).start()

    def run_flash(self, device):
        ok = write_iso(
            self.iso,
            device,
            verify=self.verify.get(),
            progress_cb=lambda v: self.after(0, self.progress.set, v),
            status_cb=lambda s: self.after(0, self.status.configure, {"text": s})
        )

        self.after(0, self.finish, ok)

    def finish(self, ok):
        self.btn.configure(state="normal", text="⚡ FLASH USB")
        if ok:
            self.status.configure(text="✅ Success!", text_color=COLOR_SUCCESS)
            self.progress.set(1.0)
            messagebox.showinfo("Done", "USB drive is ready to use!")
        else:
            self.status.configure(text="❌ Verification Failed", text_color=COLOR_DANGER)
            messagebox.showerror("Error", "Hash mismatch! The write may have failed.")

### MAIN ### 
if __name__ == "__main__":
    app = VioletBootApp()
    app.mainloop()
    