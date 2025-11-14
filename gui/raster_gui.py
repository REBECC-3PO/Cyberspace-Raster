import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from rasterize import process_folder, PALETTES

# --- default input/output folders next to this script ---

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = SCRIPT_DIR / "input"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "output"

# make sure they exist
DEFAULT_INPUT_DIR.mkdir(exist_ok=True)
DEFAULT_OUTPUT_DIR.mkdir(exist_ok=True)

# --- basic color theme (VT320-ish dark mode) ---
BG      = "#0b0500"   # background
PANEL   = "#170800"   # panels / entries
FG      = "#ff9a10"   # main text
BTN_BG  = "#241008"   # buttons
BTN_FG  = "#ff9a10"
FONT    = ("C64 Pro Mono", 10)
TITLE_FONT = ("C64 Pro Mono", 16, "bold")
CLOSE_ICON_FONT = ("C64 Pro Mono", 20)   # or 20, or 24
ABOUT_ICON_FONT = ("C64 Pro Mono", 16)   # or 20, or 24

def browse_input():
    start_dir = input_var.get() or str(DEFAULT_INPUT_DIR)
    folder = filedialog.askdirectory(title="Select input folder",
                                     initialdir=start_dir)
    if folder:
        input_var.set(folder)

def browse_output():
    start_dir = output_var.get() or str(DEFAULT_OUTPUT_DIR)
    folder = filedialog.askdirectory(title="Select output folder",
                                     initialdir=start_dir)
    if folder:
        output_var.set(folder)


def show_about():
    messagebox.showinfo(
        "About Cyberspace Rasterizer",
        "Cyberspace Rasterizer\n"
        "v0.1\n\n"
        "Offline image rasterizer inspired by Cyberspace\n"
        "Dithers images into VT320-style palettes for use on your cyberdeck\n"
        "or where ever your heart pleases."
    )

def run_rasterizer():
    in_dir = input_var.get().strip()
    out_dir = output_var.get().strip()
    palette = palette_var.get().strip()
    width_text = width_var.get().strip()

    if not in_dir:
        messagebox.showerror("Error", "Please choose an input folder.")
        return
    if not out_dir:
        messagebox.showerror("Error", "Please choose an output folder.")
        return
    if palette not in PALETTES:
        messagebox.showerror("Error", f"Unknown palette '{palette}'.")
        return

    # width: allow empty for "auto"
    target_width = None
    if width_text:
        try:
            target_width = int(width_text)
            if target_width <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Width must be a positive integer, or left blank.")
            return

    in_path = Path(in_dir)
    if not in_path.is_dir():
        messagebox.showerror("Error", f"Input folder does not exist:\n{in_dir}")
        return

    Path(out_dir).mkdir(parents=True, exist_ok=True)

    status_var.set("Status: Processing…")
    root.update_idletasks()

    try:
        process_folder(
            input_dir=in_dir,
            output_dir=out_dir,
            palette_name=palette,
            target_width=target_width,
            matrix_size=8,    # keep your current default
        )
    except Exception as e:
        messagebox.showerror("Error while processing", str(e))
        status_var.set("Status: Error")
        return

    status_var.set("Status: Done!")
    messagebox.showinfo("Done", "Rasterization complete.")

# --- window drag support ---

def start_move(event):
    root._drag_start_x = event.x
    root._drag_start_y = event.y

def do_move(event):
    x = event.x_root - root._drag_start_x
    y = event.y_root - root._drag_start_y
    root.geometry(f"+{x}+{y}")

# --- build the UI ---

root = tk.Tk()
root.title("Cyberspace Rasterizer")
root.configure(bg=BG)
root.overrideredirect(True)

# drag bindings (left mouse button)
root.bind("<ButtonPress-1>", start_move)
root.bind("<B1-Motion>", do_move)

# allow ESC to close the app
root.bind("<Escape>", lambda e: root.destroy())



try:
    root.iconbitmap("cyberspace_ico.ico")  # Windows .ico
except Exception:
    # Fallback for systems that don't like iconbitmap
    try:
        icon_img = tk.PhotoImage(file="cyberspace_ico.png")
        root.iconphoto(True, icon_img)
    except Exception:
        pass


# allow a little padding
pad = {"padx": 8, "pady": 4}

input_var   = tk.StringVar(value=str(DEFAULT_INPUT_DIR))
output_var  = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))
palette_var = tk.StringVar(value="VT320")
width_var   = tk.StringVar(value="330")
status_var  = tk.StringVar(value="Status: Idle")


logo_path = "cyberspace_logo.png"
logo_img = None
if os.path.exists(logo_path):
    try:
        logo_img = tk.PhotoImage(file=logo_path)
    except Exception:
        logo_img = None

# --- top bar (about icon, logo, close button) ---

top_bar = tk.Frame(root, bg=BG)
top_bar.grid(row=0, column=0, columnspan=3, sticky="we")
top_bar.columnconfigure(1, weight=1)  # center column expands

# About button: little triangle on the left
about_btn = tk.Button(
    top_bar,
    text="⚠",
    command=show_about,
    bg=BG,
    fg=FG,
    activebackground=BG,
    activeforeground=FG,
    borderwidth=0,
    font=ABOUT_ICON_FONT
)
about_btn.grid(row=0, column=0, sticky="w", padx=8, pady=8)

# Logo / title in the center
if logo_img is not None:
    title_label = tk.Label(top_bar, image=logo_img, bg=BG)
    title_label.image = logo_img  # keep reference
else:
    title_label = tk.Label(top_bar, text="Cyberspace Raster", bg=BG, fg=FG,
                           font=TITLE_FONT)

title_label.grid(row=0, column=1, pady=(10, 10))

# Close button on the right
close_btn = tk.Button(
    top_bar,
    text="✕",
    command=root.destroy,
    bg=BG,
    fg=FG,
    activebackground=BG,
    activeforeground=FG,
    borderwidth=0,
    font=CLOSE_ICON_FONT
)
close_btn.grid(row=0, column=2, sticky="e", padx=8, pady=8)



# row 1: input folder
lbl_in = tk.Label(root, text="Input folder:", bg=BG, fg=FG, font=FONT)
lbl_in.grid(row=1, column=0, sticky="e", **pad)

ent_in = tk.Entry(root, textvariable=input_var, bg=PANEL, fg=FG,
                  insertbackground=FG, font=FONT, width=40, borderwidth=1, relief="solid")
ent_in.grid(row=1, column=1, sticky="we", **pad)

btn_in = tk.Button(root, text="Browse…", command=browse_input,
                   bg=BTN_BG, fg=BTN_FG, activebackground=BTN_BG, activeforeground=BTN_FG,
                   font=FONT)
btn_in.grid(row=1, column=2, sticky="w", **pad)

# row 2: output folder
lbl_out = tk.Label(root, text="Output folder:", bg=BG, fg=FG, font=FONT)
lbl_out.grid(row=2, column=0, sticky="e", **pad)

ent_out = tk.Entry(root, textvariable=output_var, bg=PANEL, fg=FG,
                   insertbackground=FG, font=FONT, width=40, borderwidth=1, relief="solid")
ent_out.grid(row=2, column=1, sticky="we", **pad)

btn_out = tk.Button(root, text="Browse…", command=browse_output,
                    bg=BTN_BG, fg=BTN_FG, activebackground=BTN_BG, activeforeground=BTN_FG,
                    font=FONT)
btn_out.grid(row=2, column=2, sticky="w", **pad)

# row 3: palette dropdown
palette_options = sorted(PALETTES.keys())
palette_btn = tk.Menubutton(
    root,
    textvariable=palette_var,
    bg=PANEL,
    fg=FG,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    font=FONT,
    relief="solid",      # or "flat" if you want no border
    borderwidth=1,
    highlightthickness=0
)

# dropdown menu part
palette_menu = tk.Menu(
    palette_btn,
    tearoff=0,
    bg=PANEL,
    fg=FG,
    activebackground=BTN_BG,
    activeforeground=BTN_FG,
    borderwidth=1,
    relief="solid"
)

for name in palette_options:
    palette_menu.add_radiobutton(
        label=name,
        variable=palette_var,
        value=name,
        selectcolor=PANEL   # keeps the radio mark from being bright/ugly
    )

palette_btn.configure(menu=palette_menu)
palette_btn.grid(row=3, column=1, sticky="w", **pad)

arrow_lbl = tk.Label(
    root,
    text="▼",
    bg=PANEL,
    fg=FG,
    font=FONT
)
arrow_lbl.grid(row=3, column=1, sticky="e", padx=(0, 430))  # tweak padding as needed



# row 4: width
lbl_width = tk.Label(root, text="Width (px, optional):", bg=BG, fg=FG, font=FONT)
lbl_width.grid(row=4, column=0, sticky="e", **pad)

ent_width = tk.Entry(root, textvariable=width_var, bg=PANEL, fg=FG,
                     insertbackground=FG, font=FONT, width=10, borderwidth=1, relief="solid")
ent_width.grid(row=4, column=1, sticky="w", **pad)

# row 5: run button
btn_run = tk.Button(root, text="Process images", command=run_rasterizer,
                    bg=BTN_BG, fg=BTN_FG, activebackground=BTN_BG, activeforeground=BTN_FG,
                    font=("Consolas", 11, "bold"))
btn_run.grid(row=5, column=0, columnspan=3, pady=(12, 6))

# row 6: status
lbl_status = tk.Label(root, textvariable=status_var, bg=BG, fg=FG, font=FONT)
lbl_status.grid(row=6, column=0, columnspan=3, pady=(0, 10))

# make the middle column stretch
root.columnconfigure(1, weight=1)

root.mainloop()
