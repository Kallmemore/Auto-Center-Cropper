import os
import sys
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except:
    DND_FILES = None
    TkinterDnD = None

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps

SUPPORTED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
DEFAULT_WIDTH = 880
DEFAULT_HEIGHT = 1240

# ================= Image Processing =================
def resize_if_needed(img, target_width, target_height):
    w, h = img.size
    scale = max(target_width / w, target_height / h, 1)
    if scale > 1:
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    return img

def center_crop(img, target_width, target_height):
    w, h = img.size
    left = (w - target_width)//2
    top = (h - target_height)//2
    right = left + target_width
    bottom = top + target_height
    return img.crop((left, top, right, bottom))

def process_file(input_path, output_dir, width, height):
    try:
        img = Image.open(input_path)
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img = resize_if_needed(img, width, height)
        cropped = center_crop(img, width, height)
        filename = os.path.basename(input_path)
        output_path = os.path.join(output_dir, filename)
        cropped.save(output_path, quality=100, subsampling=0, optimize=True)
        return True
    except Exception as e:
        print(f"ERROR: {input_path} -> {e}")
        return False

def process_all(files, output_dir, width, height, progress_callback=None):
    all_files = []
    for path in files:
        if os.path.isdir(path):
            for file in os.listdir(path):
                f = os.path.join(path, file)
                if f.lower().endswith(SUPPORTED_EXTENSIONS):
                    all_files.append(f)
        elif path.lower().endswith(SUPPORTED_EXTENSIONS):
            all_files.append(path)
    
    total = len(all_files)
    count = 0
    for f in all_files:
        if process_file(f, output_dir, width, height):
            count += 1
        if progress_callback:
            progress_callback(count, total)
    return count

# ================= Drop-on-Icon Mode =================
def drop_on_exe_mode(files, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    output_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    processed = process_all(files, output_dir, width, height)
    print(f"{processed} image(s) processed. Output folder: {output_dir}")

# ================= GUI Functions =================
def add_files():
    paths = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
    for path in paths:
        if path not in file_list.get(0, tk.END):
            file_list.insert(tk.END, path)

def add_folder():
    folder = filedialog.askdirectory()
    if folder and folder not in file_list.get(0, tk.END):
        file_list.insert(tk.END, folder)

def remove_selected():
    selected = file_list.curselection()
    for index in reversed(selected):
        file_list.delete(index)

def drop_files(event):
    paths = root.tk.splitlist(event.data)
    for path in paths:
        path = path.strip('{}')
        if os.path.exists(path) and path not in file_list.get(0, tk.END):
            file_list.insert(tk.END, path)

def update_progress(count, total):
    if total == 0:
        progress_var.set(0)
        progress_label.config(text="")
        return
    percent = int(count / total * 100)
    progress_var.set(percent)
    progress_label.config(text=f"{percent}%")
    root.update_idletasks()

def start_crop():
    output_dir = output_var.get()
    if not output_dir:
        use_default = messagebox.askyesno(
            "Warning",
            "Output folder not selected!\nDo you want to use script location as default?"
        )
        if not use_default:
            return  # Cancel
        output_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        output_var.set(output_dir)
        
    try:
        width = int(width_var.get())
        height = int(height_var.get())
    except ValueError:
        messagebox.showerror("Error", "Width and Height must be integers!")
        return

    files = file_list.get(0, tk.END)
    if not files:
        messagebox.showerror("Error", "Add at least one file or folder!")
        return

    progress_var.set(0)
    processed = process_all(files, output_dir, width, height, progress_callback=update_progress)
    progress_var.set(100)
    progress_label.config(text="COMPLETED!")
    messagebox.showinfo("Done", f"{processed} image(s) processed successfully!\nOutput folder: {output_dir}")

def select_output():
    folder = filedialog.askdirectory()
    if folder:
        output_var.set(folder)

# ================= Main GUI =================
def run_gui():
    global root, file_list, output_var, width_var, height_var, progress_var, progress_label
    if TkinterDnD:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    root.title("Auto Center Crop GUI")
    root.geometry("700x680")
    root.resizable(True, True)

    # Listbox + Scrollbar
    tk.Label(root, text="Files/Folders:").pack(pady=(10,0))
    frame_list = tk.Frame(root)
    scrollbar = tk.Scrollbar(frame_list, orient=tk.VERTICAL)
    file_list = tk.Listbox(frame_list, selectmode=tk.EXTENDED, width=90, height=20, yscrollcommand=scrollbar.set)
    scrollbar.config(command=file_list.yview)
    scrollbar.pack(side="right", fill="y")
    file_list.pack(side="left", fill="both", expand=True)
    frame_list.pack(pady=5, fill="both", expand=True)

    # Buttons
    btn_frame = tk.Frame(root)
    tk.Button(btn_frame, text="Add Files", command=add_files).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Add Folder", command=add_folder).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Remove Selected", command=remove_selected).pack(side="left", padx=5)
    btn_frame.pack(pady=5)

    # Output folder
    output_var = tk.StringVar()
    tk.Label(root, text="Output Folder:").pack(pady=(10,0))
    tk.Entry(root, textvariable=output_var, width=60).pack()
    tk.Button(root, text="Browse", command=select_output).pack(pady=5)

    # Resolution
    width_var = tk.StringVar(value=str(DEFAULT_WIDTH))
    height_var = tk.StringVar(value=str(DEFAULT_HEIGHT))
    tk.Label(root, text="Output Width x Height:").pack(pady=(10,0))
    res_frame = tk.Frame(root)
    tk.Entry(res_frame, textvariable=width_var, width=8).pack(side="left", padx=(0,5))
    tk.Label(res_frame, text="x").pack(side="left")
    tk.Entry(res_frame, textvariable=height_var, width=8).pack(side="left", padx=(5,0))
    res_frame.pack(pady=5)

    # Progress Bar with label
    progress_var = tk.IntVar()
    progress_bar_frame = tk.Frame(root)
    progress_bar_frame.pack(pady=10)
    progress_bar = ttk.Progressbar(progress_bar_frame, variable=progress_var, maximum=100, length=600)
    progress_bar.pack()
    progress_label = tk.Label(progress_bar_frame, text="", fg="green", font=("Arial", 12, "bold"))
    progress_label.place(relx=0.5, rely=0.5, anchor="center")  # وسط Progressbar

    # Start button
    tk.Button(root, text="START CROP", height=2, width=30, command=start_crop).pack(pady=15)

    # Drag & Drop
    if TkinterDnD:
        file_list.drop_target_register(DND_FILES)
        file_list.dnd_bind('<<Drop>>', drop_files)

    root.mainloop()

# ================= Main =================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        drop_on_exe_mode(sys.argv[1:])
    else:
        run_gui()
