"""
StoreLens AI - Video & Thumbnail Processing
Extracts high-resolution frames at specified video timestamps via FFmpeg / OpenCV
and applies studio enhancements without cropping packaging text.
"""
import os
import subprocess
import cv2
from PIL import Image, ImageEnhance, ImageOps

STATIC_THUMBNAILS = os.path.join(os.path.dirname(__file__), "static", "thumbnails")
os.makedirs(STATIC_THUMBNAILS, exist_ok=True)

def extract_frame(video_path: str, timestamp_sec: float, output_filename: str) -> str:
    """
    Extracts a video frame at `timestamp_sec` using FFmpeg with OpenCV fallback.
    Returns the relative URL to the static thumbnail.
    """
    output_path = os.path.join(STATIC_THUMBNAILS, output_filename)
    success = False
    
    # 1. Try FFmpeg extraction first
    try:
        ts = max(0.0, float(timestamp_sec))
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{ts:.2f}",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 500:
            success = True
    except Exception as e:
        print(f"FFmpeg frame extraction note: {e}")

    # 2. Try OpenCV fallback if FFmpeg didn't produce the image
    if not success:
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_idx = int(timestamp_sec * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            if ret and frame is not None:
                cv2.imwrite(output_path, frame)
                success = True
            cap.release()
        except Exception as e:
            print(f"OpenCV fallback error: {e}")

    # 3. Post-process image with padding to preserve full packaging and text
    if success and os.path.exists(output_path):
        enhance_studio_frame(output_path)
        
    return f"/static/thumbnails/{output_filename}"

def enhance_studio_frame(image_path: str) -> None:
    """
    Enhances contrast and sharpness, and pads onto a clean neutral canvas (#09090b)
    so vertical boxes and text are never cropped off.
    """
    try:
        with Image.open(image_path) as im:
            rgb_im = im.convert("RGB")
            
            # Subtle contrast and sharpness boost
            enhancer = ImageEnhance.Contrast(rgb_im)
            rgb_im = enhancer.enhance(1.08)
            
            sharpener = ImageEnhance.Sharpness(rgb_im)
            rgb_im = sharpener.enhance(1.15)
            
            # Pad onto neutral 640x480 canvas instead of cropping
            target_w, target_h = 640, 480
            padded_im = ImageOps.pad(
                rgb_im,
                (target_w, target_h),
                method=Image.Resampling.LANCZOS,
                color=(9, 9, 11),  # #09090b deep neutral black
                centering=(0.5, 0.5)
            )
            
            padded_im.save(image_path, "JPEG", quality=92)
    except Exception as e:
        print(f"Studio enhancement notice: {e}")
