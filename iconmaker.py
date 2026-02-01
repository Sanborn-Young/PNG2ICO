import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

# -----------------------------------------
# Utility: ensure output directory exists
# -----------------------------------------
def ensure_output_dir():
    output_dir = os.path.join(os.getcwd(), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

# -----------------------------------------
# Utility: pad image to square with transparency
# -----------------------------------------
def pad_to_square(img):
    w, h = img.size
    if w == h:
        return img  # already square

    max_side = max(w, h)
    new_img = Image.new("RGBA", (max_side, max_side), (0, 0, 0, 0))
    new_img.paste(img, ((max_side - w) // 2, (max_side - h) // 2))
    return new_img

# -----------------------------------------
# Convert white → transparent (with tolerance)
# -----------------------------------------
def convert_white_to_transparent(img, tolerance=10):
    img = img.convert("RGBA")
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]

            # Check if pixel is near white
            if (r >= 255 - tolerance and
                g >= 255 - tolerance and
                b >= 255 - tolerance):
                pixels[x, y] = (255, 255, 255, 0)  # transparent

    return img

# -----------------------------------------
# Checkerboard background generator
# -----------------------------------------
def make_checkerboard(size, block=8):
    """Create a checkerboard background to visualize transparency."""
    bg = Image.new("RGB", size, "white")
    pixels = bg.load()

    for y in range(size[1]):
        for x in range(size[0]):
            if ((x // block) + (y // block)) % 2 == 0:
                pixels[x, y] = (200, 200, 200)  # light gray
            else:
                pixels[x, y] = (255, 255, 255)  # white

    return bg

# -----------------------------------------
# Multi-size preview window
# -----------------------------------------
def show_multi_preview(img):
    """Show all icon sizes side-by-side with transparency checkerboards."""
    sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]

    win = tk.Toplevel()
    win.title("Multi-Size Icon Preview")
    
    frame = tk.Frame(win)
    frame.pack(padx=10, pady=10)

    for size in sizes:
        # Resize icon
        resized = img.resize(size, Image.LANCZOS)

        # Create checkerboard background
        bg = make_checkerboard(size)

        # Composite icon on top
        bg.paste(resized, (0, 0), resized)

        # Convert to Tk image
        tk_img = ImageTk.PhotoImage(bg)

        # Create a container frame
        cell = tk.Frame(frame)
        cell.pack(side="left", padx=10)

        # Image label
        lbl = tk.Label(cell, image=tk_img)
        lbl.image = tk_img  # Keep reference
        lbl.pack()

        # Text label
        tk.Label(cell, text=f"{size[0]}×{size[1]}").pack()

    # Add continue button
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    
    btn = tk.Button(btn_frame, text="Continue", command=win.destroy, width=15)
    btn.pack()
    
    # Make modal and wait
    win.grab_set()
    win.wait_window()

# -----------------------------------------
# Convert to ICO with high-quality resizing
# -----------------------------------------
def convert_to_ico(image_path, output_dir, remove_white):
    try:
        img = Image.open(image_path).convert("RGBA")

        # Optional white→transparent conversion
        if remove_white:
            img = convert_white_to_transparent(img)

        # Pad to square
        img = pad_to_square(img)

        # Define icon sizes (DPI-aware)
        sizes = [
            (16, 16),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256)
        ]

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_dir, base_name + '.ico')

        # CRITICAL FIX: Use sizes parameter ONLY - let Pillow do the resizing
        img.save(
            output_path,
            format='ICO',
            sizes=sizes
        )

        return output_path, None  # Success: return path and no error

    except Exception as e:
        return None, str(e)  # Failure: return no path and error message

# -----------------------------------------
# Single-image preview window
# -----------------------------------------
def show_preview(image_path):
    preview_win = tk.Toplevel()
    preview_win.title("Image Preview")

    img = Image.open(image_path)
    img = pad_to_square(img)

    # Scale preview to max 300px
    preview_size = 300
    img.thumbnail((preview_size, preview_size), Image.LANCZOS)

    tk_img = ImageTk.PhotoImage(img)

    label = tk.Label(preview_win, image=tk_img)
    label.image = tk_img  # keep reference
    label.pack(padx=10, pady=10)
    
    # Add continue button
    btn = tk.Button(preview_win, text="Continue", command=preview_win.destroy, width=15)
    btn.pack(pady=10)
    
    # Make modal and wait
    preview_win.grab_set()
    preview_win.wait_window()

# -----------------------------------------
# Main GUI
# -----------------------------------------
def main_gui():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title='Select an image file to convert to ICO',
        filetypes=[
            ('Image Files', '*.png *.jpg *.jpeg *.bmp *.gif *.tiff'),
            ('PNG files', '*.png'),
            ('JPEG files', '*.jpg *.jpeg'),
            ('All files', '*.*')
        ]
    )

    if not file_path:
        messagebox.showinfo('No Selection', 'No file was selected. Exiting.')
        root.destroy()
        return

    # Show preview window
    show_preview(file_path)

    # Show multi-size preview window
    img = Image.open(file_path).convert("RGBA")
    img = pad_to_square(img)
    show_multi_preview(img)

    # Ask user if they want white→transparent conversion
    remove_white = messagebox.askyesno(
        "White Background Removal",
        "Do you want to convert white (or near‑white) pixels to transparent?"
    )

    output_dir = ensure_output_dir()
    output_path, error = convert_to_ico(file_path, output_dir, remove_white)

    if output_path and os.path.exists(output_path):
        messagebox.showinfo(
            'Conversion Complete',
            f'Icon file successfully created!\n\n'
            f'Location:\n{output_dir}\n\n'
            f'Included sizes:\n'
            f'• 16×16\n'
            f'• 32×32\n'
            f'• 48×48\n'
            f'• 64×64\n'
            f'• 128×128\n'
            f'• 256×256\n\n'
            f'White→Transparent: {"Enabled" if remove_white else "Disabled"}'
        )
    else:
        messagebox.showerror('Conversion Error', f'Failed to convert image:\n{error}')

    root.destroy()

if __name__ == '__main__':
    main_gui()
