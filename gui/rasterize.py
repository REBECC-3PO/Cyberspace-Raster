from PIL import Image
import numpy as np
import sys
from pathlib import Path



# ---------- DITHERING CORE ----------

def bayer_matrix(n: int) -> np.ndarray:
    """Generate an n x n Bayer (ordered dither) matrix. n must be a power of 2."""
    if n == 1:
        return np.array([[0]], dtype=np.float32)

    m2 = bayer_matrix(n // 2)

    tl = 4 * m2
    tr = 4 * m2 + 2
    bl = 4 * m2 + 3
    br = 4 * m2 + 1

    top = np.concatenate((tl, tr), axis=1)
    bottom = np.concatenate((bl, br), axis=1)
    return np.concatenate((top, bottom), axis=0)

# Named color palettes: (background_color, foreground_color)
PALETTES = {
    "vt320": ((23, 8, 0), (255, 154, 16)),
    "paper": ((255, 244, 210), (0, 0, 0)),
    "matrix": ((0, 0, 0), (140, 255, 140)),
    "amber": ((0, 0, 0), (255, 152, 56)),  
    "green_phosphor": ((0, 0, 0), (0, 255, 128)),
    "c64": ((0, 0, 170), (255, 255, 85)),
}



def rasterize(input_path: str,
              output_path: str,
              palette_name: str = "vt320",
              matrix_size: int = 8,
              target_width: int | None = None):
    """Process a single image file."""
    img = Image.open(input_path).convert("L")

    # optional resize
    if target_width is not None:
        w, h = img.size
        new_h = int(h * (target_width / w))
        img = img.resize((target_width, new_h), Image.LANCZOS)

    w, h = img.size
    gray = np.array(img, dtype=np.float32) / 255.0  # values 0..1

    # --- tonal shaping to get solid dark silhouettes ---

    gamma = 1.1          # slight contrast tweak
    shadow_cutoff = 0.28 # anything below this becomes pure background

    # apply gamma curve
    gray_lin = np.power(gray, gamma)

    # mark deep shadows
    shadows = gray_lin < shadow_cutoff

    # rescale the remaining range back to 0..1
    gray_scaled = (gray_lin - shadow_cutoff) / (1.0 - shadow_cutoff)
    gray_scaled = np.clip(gray_scaled, 0.0, 1.0)

    # --- Bayer matrix tiled across the image ---

    M = bayer_matrix(matrix_size)
    M = (M + 0.5) / (matrix_size * matrix_size)     # normalize 0..1
    tiled = np.tile(M, (h // matrix_size + 1, w // matrix_size + 1))
    tiled = tiled[:h, :w]

    # primary dither mask using the adjusted gray
    mask = gray_scaled >= tiled

    # force deep shadows to be background only
    mask[shadows] = False

    # --- apply palette to build RGB image ---

    bg, fg = PALETTES[palette_name]
    out = np.zeros((h, w, 3), dtype=np.uint8)
    out[~mask] = bg
    out[mask] = fg

    Image.fromarray(out, mode="RGB").save(output_path)
    print(f"Saved {output_path} ({w}x{h}, palette={palette_name})")

# ---------- FOLDER BATCH PROCESSING ----------

def process_folder(input_dir: str,
                   output_dir: str,
                   palette_name: str = "vt320",
                   target_width: int | None = None,
                   matrix_size: int = 8):
    in_path = Path(input_dir)
    out_path = Path(output_dir)

    if not in_path.is_dir():
        print(f"Input folder '{input_dir}' does not exist.")
        sys.exit(1)

    out_path.mkdir(parents=True, exist_ok=True)

    # extensions we’ll treat as images
    exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}

    for file in sorted(in_path.iterdir()):
        if not file.is_file():
            continue
        if file.suffix.lower() not in exts:
            continue

        # basename + _style.png
        output_name = f"{file.stem}_{palette_name}.png"
        output_path = out_path / output_name

        print(f"Processing {file.name} -> {output_name}")
        rasterize(
            str(file),
            str(output_path),
            palette_name=palette_name,
            matrix_size=matrix_size,
            target_width=target_width,
        )

# ---------- COMMAND LINE INTERFACE ----------

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python rasterize.py input_folder output_folder [vt320|matrix|paper] [width]")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    palette = sys.argv[3] if len(sys.argv) > 3 else "vt320"
    width = int(sys.argv[4]) if len(sys.argv) > 4 else None

    if palette not in PALETTES:
        print(f"Unknown palette '{palette}'. Choose from: {', '.join(PALETTES.keys())}")
        sys.exit(1)

    process_folder(input_folder, output_folder, palette_name=palette, target_width=width)
