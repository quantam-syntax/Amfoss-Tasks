import re
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

ASSETS = Path("assets")
OUTPUT = Path("treasure_path.png")

MAX_CANVAS = 2000
MARGIN = 60
TELEPORT_THRESHOLD = 0.02  # % of visible pixels needed to count as a real block


def get_asset_files(folder: Path):
    """Grab all numbered image files like 001_something.png and sort them by number."""
    pattern = re.compile(r"^0*([0-9]+)_.*\.(png|jpg|jpeg)$", re.IGNORECASE)
    files = []
    for f in folder.iterdir():
        match = pattern.match(f.name)
        if match:
            files.append((int(match.group(1)), f))
    files.sort(key=lambda x: x[0])
    return [p for _, p in files]


def load_image(path: Path):
    """Load an image using OpenCV, keeping transparency if it exists."""
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise RuntimeError(f"Could not load {path}")
    return img


def extract_block_info(img):
    h, w = img.shape[:2]
    if img.shape[2] == 4:
        alpha = img[:, :, 3]
        mask = (alpha > 10).astype(np.uint8) * 255
    else:
        gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            mask2 = np.zeros_like(mask)
            cv2.drawContours(mask2, [max(contours, key=cv2.contourArea)], -1, 255, -1)
            mask = mask2
    nonzero_ratio = cv2.countNonZero(mask) / (w * h)
    teleport = nonzero_ratio < TELEPORT_THRESHOLD
    if teleport:
        cx, cy = w / 2, h / 2
        mean_color = cv2.mean(img[:, :, :3])[:3]
        avg_color = (255 - int(mean_color[2]), 180, 180)
        return (cx, cy), avg_color, True
    M = cv2.moments(mask)
    cx = M["m10"] / M["m00"] if M["m00"] else w / 2
    cy = M["m01"] / M["m00"] if M["m00"] else h / 2
    mean_color = cv2.mean(img[:, :, :3], mask=mask)[:3]
    avg_color = (int(mean_color[2]), 120, 200)
    return (cx, cy), avg_color, False

def draw_map(blocks, out_file: Path):
    xs = [b["pos"][0] for b in blocks]
    ys = [b["pos"][1] for b in blocks]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    width, height = maxx - minx or 1, maxy - miny or 1
    scale = (MAX_CANVAS - 2 * MARGIN) / max(width, height)
    canvas_w = int(width * scale + 2 * MARGIN)
    canvas_h = int(height * scale + 2 * MARGIN)
    canvas = Image.new("RGB", (canvas_w, canvas_h), (230, 240, 255))
    draw = ImageDraw.Draw(canvas)
    for x in range(0, canvas_w, 50):
        draw.line([(x, 0), (x, canvas_h)], fill=(200, 220, 250), width=1)
    for y in range(0, canvas_h, 50):
        draw.line([(0, y), (canvas_w, y)], fill=(200, 220, 250), width=1)
    def to_canvas(pt):
        x, y = pt
        return (int((x - minx) * scale + MARGIN), int((y - miny) * scale + MARGIN))
    radius = max(6, int(min(canvas_w, canvas_h) / 120))
    thickness = max(3, int(min(canvas_w, canvas_h) / 150))
    prev = None
    for b in blocks:
        if prev and not prev["teleport"] and not b["teleport"]:
            draw.line([to_canvas(prev["pos"]), to_canvas(b["pos"])],
                      fill=(50, 50, 180), width=thickness)
        prev = b
    for i, b in enumerate(blocks, start=1):
        x, y = to_canvas(b["pos"])
        if b["teleport"]:
            draw.rectangle([x - radius, y - radius, x + radius, y + radius],
                           outline=(100, 100, 100), width=3)
        else:
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=b["color"])
            inner = max(1, radius // 3)
            draw.ellipse([x - inner, y - inner, x + inner, y + inner], fill=(255, 255, 255))
        draw.text((x + radius + 6, y - (radius + 6)), str(i), fill=(10, 10, 40))
    canvas.save(out_file)

def draw_map(blocks, out_file: Path):
    """Draw all the blocks onto one treasure map image."""
    xs = [b["pos"][0] for b in blocks]
    ys = [b["pos"][1] for b in blocks]

    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    width, height = maxx - minx or 1, maxy - miny or 1

    scale = (MAX_CANVAS - 2 * MARGIN) / max(width, height)
    canvas_w = int(width * scale + 2 * MARGIN)
    canvas_h = int(height * scale + 2 * MARGIN)

    canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    def to_canvas(pt):
        x, y = pt
        return (int((x - minx) * scale + MARGIN), int((y - miny) * scale + MARGIN))

    radius = max(6, int(min(canvas_w, canvas_h) / 120))
    thickness = max(3, int(min(canvas_w, canvas_h) / 150))

    prev = None
    for b in blocks:
        if prev and not prev["teleport"] and not b["teleport"]:
            draw.line([to_canvas(prev["pos"]), to_canvas(b["pos"])],
                      fill=prev["color"], width=thickness)
        prev = b

    for i, b in enumerate(blocks, start=1):
        x, y = to_canvas(b["pos"])
        if b["teleport"]:
            draw.ellipse([x - radius, y - radius, x + radius, y + radius],
                         outline=(120, 120, 120), width=2)
            draw.line([(x - radius, y - radius), (x + radius, y + radius)], fill=(120, 120, 120), width=2)
            draw.line([(x - radius, y + radius), (x + radius, y - radius)], fill=(120, 120, 120), width=2)
        else:
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=b["color"])
            inner = max(1, radius // 3)
            draw.ellipse([x - inner, y - inner, x + inner, y + inner], fill=(255, 255, 255))
        draw.text((x + radius + 4, y - (radius + 6)), str(i), fill=(0, 0, 0))

    canvas.save(out_file)


def main():
    if not ASSETS.exists():
        print("⚠️ No assets/ folder found.")
        return

    files = get_asset_files(ASSETS)
    if not files:
        print("⚠️ No matching images found in assets/.")
        return

    print(f"Found {len(files)} images. Building map...")

    blocks = []
    for f in files:
        img = load_image(f)
        pos, color, teleport = extract_block_info(img)
        blocks.append({"file": f.name, "pos": pos, "color": color, "teleport": teleport})
        print(f" - {f.name} → pos=({pos[0]:.1f},{pos[1]:.1f}) color={color} teleport={teleport}")

    draw_map(blocks, OUTPUT)
    print(f"\n✅ Treasure map saved as {OUTPUT.resolve()}")
    print(f"   Blocks: {len(blocks)} (teleports: {sum(b['teleport'] for b in blocks)})")


if __name__ == "__main__":
    main()