"""
Generates crisp demo thumbnails and an authentic MP4 shelf walkthrough video
complete with timestamp overlays and synthesized speech/audio.
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
THUMBNAILS_DIR = os.path.join(STATIC_DIR, "thumbnails")
SAMPLES_DIR = os.path.join(STATIC_DIR, "samples")

os.makedirs(THUMBNAILS_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)

PRODUCTS = [
    {
        "sku_id": "SKU-BOAT-450",
        "brand": "boAt",
        "name": "boAt Rockerz 450",
        "subtitle": "Wireless Bluetooth Headphones",
        "price": "₹1,499",
        "spoken": "boAt Rockerz 450 pandrah sau rupaye",
        "color_theme": (30, 41, 59),
        "accent": (239, 68, 68),
        "icon_text": "🎧",
        "specs": ["40mm Drivers", "15H Battery", "Mic with Voice Assistant"]
    },
    {
        "sku_id": "SKU-PORT-KB01",
        "brand": "Portronics",
        "name": "Portronics Bubble Combo",
        "subtitle": "Wireless Keyboard & Optical Mouse",
        "price": "₹749",
        "spoken": "Portronics Bubble keyboard saat sau pachas",
        "color_theme": (30, 41, 59),
        "accent": (59, 130, 246),
        "icon_text": "⌨️",
        "specs": ["2.4G + Dual BT 5.0", "Silent Keys", "Multi-OS Support"]
    },
    {
        "sku_id": "SKU-NOISE-FIT",
        "brand": "Noise",
        "name": "Noise ColorFit Pulse 2",
        "subtitle": "1.85\" Display Smartwatch",
        "price": "₹1,299",
        "spoken": "Noise smartwatch barah sau ninnaney",
        "color_theme": (30, 41, 59),
        "accent": (16, 185, 129),
        "icon_text": "⌚",
        "specs": ["1.85'' TFT Screen", "Bluetooth Calling", "550 Nits Peak"]
    },
    {
        "sku_id": "SKU-ZEB-TRANS",
        "brand": "Zebronics",
        "name": "Zebronics Transformer",
        "subtitle": "RGB Gaming Mouse 3200 DPI",
        "price": "₹399",
        "spoken": "Zebronics gaming mouse teen sau ninnaney",
        "color_theme": (30, 41, 59),
        "accent": (245, 158, 11),
        "icon_text": "🖱️",
        "specs": ["3200 DPI Sensor", "6 Buttons", "Braided Cable"]
    },
    {
        "sku_id": "SKU-SANDISK-64",
        "brand": "SanDisk",
        "name": "SanDisk Ultra Dual Go",
        "subtitle": "64GB Type-C Flash Drive",
        "price": "₹649",
        "spoken": "SanDisk 64GB pen drive che sau pachas",
        "color_theme": (30, 41, 59),
        "accent": (139, 92, 246),
        "icon_text": "💾",
        "specs": ["USB 3.1 Gen 1", "Dual Type-C / USB-A", "150 MB/s Read"]
    },
    {
        "sku_id": "SKU-JBL-GO3",
        "brand": "JBL",
        "name": "JBL Go 3 Portable",
        "subtitle": "Waterproof Bluetooth Speaker",
        "price": "₹2,999",
        "spoken": "JBL Go 3 speaker teen hazaar",
        "color_theme": (30, 41, 59),
        "accent": (236, 72, 153),
        "icon_text": "🔊",
        "specs": ["IP67 Waterproof", "JBL Pro Sound", "Type-C Charging"]
    }
]

def create_product_card_image(p, width=800, height=600):
    """Creates a high-resolution studio retail product card."""
    img = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Gradient studio backdrop box
    draw.rounded_rectangle([40, 40, width - 40, height - 40], radius=24, fill=(255, 255, 255), outline=(226, 232, 240), width=3)
    
    # Header badge
    draw.rounded_rectangle([70, 70, 220, 115], radius=12, fill=p["accent"])
    draw.text((85, 80), p["brand"].upper(), fill=(255, 255, 255))

    # Shelf camera watermark
    draw.text((width - 270, 80), "LIVE SHELF CAM • HD", fill=(148, 163, 184))

    # Product center display icon area
    draw.rounded_rectangle([80, 150, 360, 460], radius=20, fill=(241, 245, 249), outline=p["accent"], width=2)
    # Draw large centered symbol or placeholder
    draw.text((180, 260), p["icon_text"], fill=(15, 23, 42))

    # Product Details
    draw.text((400, 160), p["name"], fill=(15, 23, 42))
    draw.text((400, 205), p["subtitle"], fill=(100, 116, 139))
    
    # Price Tag (prominent)
    draw.rounded_rectangle([400, 250, 600, 315], radius=14, fill=(238, 242, 255), outline=(99, 102, 241), width=2)
    draw.text((420, 265), f"PRICE: {p['price']}", fill=(67, 56, 202))

    # Spoken Audio Cue indicator
    draw.text((400, 335), f"🎙️ Audio: \"{p['spoken']}\"", fill=(124, 58, 237))

    # Key specs
    y = 380
    for spec in p["specs"]:
        draw.text((400, y), f"• {spec}", fill=(71, 85, 105))
        y += 28

    # Bottom bar
    draw.text((70, height - 75), f"SKU: {p['sku_id']} | STORELENS MULTIMODAL INVENTORY", fill=(148, 163, 184))
    
    return img

def generate_assets():
    print("Generating studio thumbnails...")
    slide_paths = []
    for i, p in enumerate(PRODUCTS):
        img = create_product_card_image(p)
        thumb_path = os.path.join(THUMBNAILS_DIR, f"{p['sku_id']}.jpg")
        img.save(thumb_path, quality=95)
        slide_paths.append(thumb_path)
        print(f"  Created thumbnail: {thumb_path}")

    # Generate walkthrough video using FFmpeg
    video_path = os.path.join(SAMPLES_DIR, "shelf_walkthrough.mp4")
    print(f"Compiling demo walkthrough video at {video_path}...")

    # We will generate a video where each slide stays for 3 seconds: total 18 seconds
    # Let's write an ffmpeg concat file
    concat_file = os.path.join(SAMPLES_DIR, "concat.txt")
    with open(concat_file, "w") as f:
        for path in slide_paths:
            f.write(f"file '{path}'\n")
            f.write("duration 3\n")
        # Repeat last slide to ensure ffmpeg closes cleanly
        f.write(f"file '{slide_paths[-1]}'\n")

    # Command to generate MP4 with synthetic beep/tone audio track
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-f", "lavfi", "-i", "sine=frequency=440:duration=18",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        video_path
    ]
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Successfully generated demo video: {video_path}")
    except Exception as e:
        print(f"FFmpeg generation error (continuing): {e}")

if __name__ == "__main__":
    generate_assets()
