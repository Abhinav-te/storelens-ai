"""
StoreLens AI - FastAPI Backend Service
Multimodal Hyperlocal Retail Onboarding & Inventory Synchronization Platform
"""
import os
import sys
import time
import shutil
import tempfile
from typing import Optional, List

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from catalog import (
    get_catalog,
    upsert_catalog_items,
    update_item_stock,
    reset_catalog,
    load_catalog,
    DEFAULT_DEMO_ITEMS
)
from video_processor import extract_frame
from gemini_service import analyze_video_walkthrough, analyze_voice_command

app = FastAPI(
    title="StoreLens AI Backend",
    description="Multimodal Hyperlocal Retail Inventory Synchronization Platform",
    version="1.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for thumbnails and sample video
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(os.path.join(STATIC_DIR, "thumbnails"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "samples"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

SAMPLE_VIDEO_PATH = os.path.join(STATIC_DIR, "samples", "shelf_walkthrough.mp4")

# Request Models
class VoiceUpdateRequest(BaseModel):
    transcript: Optional[str] = None
    sku_id: Optional[str] = None
    action: Optional[str] = None
    quantity: Optional[int] = 1

class ResetRequest(BaseModel):
    seed: Optional[bool] = False

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "StoreLens AI Backend",
        "endpoints": [
            "POST /api/onboard-video",
            "POST /api/voice-update",
            "GET /api/catalog",
            "POST /api/reset"
        ]
    }

@app.get("/api/catalog")
def get_store_catalog(
    q: Optional[str] = Query(None, description="Search query across item name, brand, specs"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Returns the live list of store items with optional search and category filters."""
    items = get_catalog(query=q, category=category)
    return {
        "store_name": "Sharma Electronics & Gear",
        "distance_km": 0.8,
        "total_items": len(items),
        "items": items
    }

@app.post("/api/onboard-video")
async def onboard_video(
    video: Optional[UploadFile] = File(None),
    use_sample: Optional[bool] = Form(False)
):
    """
    Accepts an uploaded shelf walkthrough video (.mp4/.webm) or sample video.
    Analyzes video & audio using Gemini 3.8 Flash, extracts frames by timestamp,
    generates studio thumbnails, and saves items to the catalog.
    """
    temp_video_path = None
    target_video_path = None
    is_sample = bool(use_sample or video is None)

    try:
        if is_sample:
            if not os.path.exists(SAMPLE_VIDEO_PATH):
                raise HTTPException(status_code=404, detail="Sample walkthrough video not found.")
            target_video_path = SAMPLE_VIDEO_PATH
            print(f"[OnboardVideo] Using sample walkthrough video: {target_video_path}")
        else:
            suffix = os.path.splitext(video.filename)[1] or ".mp4"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(video.file, tmp)
                temp_video_path = tmp.name
                target_video_path = temp_video_path
            print(f"[OnboardVideo] Received video upload: {video.filename} -> {temp_video_path}")

        # 1. Analyze video walkthrough with Gemini 3.8 Flash
        extracted_items = analyze_video_walkthrough(target_video_path, use_sample=is_sample)

        # 2. Extract frame at each item's timestamp_sec and save studio thumbnail
        processed_items = []
        for idx, item in enumerate(extracted_items):
            sku_id = item.get("sku_id") or f"SKU-PROD-{idx+1:02d}"
            item["sku_id"] = sku_id
            timestamp = float(item.get("timestamp_sec", idx * 3.0))
            
            thumb_filename = f"{sku_id}.jpg"
            thumbnail_url = extract_frame(target_video_path, timestamp, thumb_filename)
            cache_buster = int(time.time())
            item["thumbnail_url"] = f"{thumbnail_url}?v={cache_buster}"
            processed_items.append(item)

        # 3. For real video uploads, clear pre-seeded catalog first so only new products appear
        if not is_sample:
            reset_catalog(seed=False)

        updated_catalog = upsert_catalog_items(processed_items)

        return {
            "success": True,
            "message": f"Extracted {len(processed_items)} items from shelf walkthrough video.",
            "extracted_count": len(processed_items),
            "items": processed_items,
            "catalog": updated_catalog
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[OnboardVideo] Error during video onboarding: {e}")
        if is_sample:
            fallback_items = upsert_catalog_items(DEFAULT_DEMO_ITEMS)
            return {
                "success": True,
                "message": f"Loaded demo items: {str(e)}",
                "extracted_count": len(fallback_items),
                "items": fallback_items,
                "catalog": fallback_items
            }
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except Exception:
                pass

@app.post("/api/voice-update")
async def voice_update(
    audio: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None)
):
    """
    Accepts merchant audio note or text transcript (e.g. 'Ek Portronics keyboard bik gaya').
    Analyzes intent via Gemini 3.8 Flash, mutates stock count immediately, and returns confirmation.
    """
    temp_audio_path = None
    try:
        if audio:
            suffix = os.path.splitext(audio.filename)[1] or ".webm"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(audio.file, tmp)
                temp_audio_path = tmp.name

        current_catalog = load_catalog()
        if not current_catalog:
            current_catalog = upsert_catalog_items(DEFAULT_DEMO_ITEMS)

        # Parse command with Gemini 3.8 Flash
        decision = analyze_voice_command(
            audio_path=temp_audio_path,
            transcript=transcript,
            current_catalog=current_catalog
        )

        sku_id = decision.get("sku_id")
        action = decision.get("action", "DECREMENT")
        quantity = int(decision.get("quantity", 1))

        if not sku_id:
            raise HTTPException(status_code=400, detail="Could not match item in store catalog.")

        # Mutate catalog stock
        updated_item, updated_catalog = update_item_stock(sku_id, action, quantity)
        if not updated_item:
            raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found in catalog.")

        item_name = updated_item.get("item_name", sku_id)
        new_stock = updated_item.get("stock_count", 0)
        action_verb = "sold" if action == "DECREMENT" else ("added" if action == "INCREMENT" else "marked sold out")
        
        raw_hinglish = decision.get("confirmation_hinglish") or (
            f"{item_name} ka stock update ho gaya. Remaining: {new_stock}."
        )
        confirmation_msg = raw_hinglish.replace("✅", "").replace("🎙️", "").strip()

        raw_en = decision.get("confirmation_en") or (
            f"{action_verb.capitalize()} {quantity} unit(s) of {item_name}. Remaining: {new_stock}."
        )
        confirmation_en = raw_en.replace("✅", "").replace("🎙️", "").strip()

        return {
            "success": True,
            "action": action,
            "quantity": quantity,
            "sku_id": sku_id,
            "item_name": item_name,
            "updated_item": updated_item,
            "message": confirmation_msg,
            "confirmation_en": confirmation_en,
            "catalog": updated_catalog
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[VoiceUpdate] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception:
                pass

@app.post("/api/reset")
def reset_store_catalog(body: Optional[ResetRequest] = None, seed: Optional[bool] = Query(None)):
    """Resets the demo catalog cleanly (either empty or pre-seeded)."""
    should_seed = False
    if seed is not None:
        should_seed = seed
    elif body is not None and body.seed is not None:
        should_seed = body.seed

    items = reset_catalog(seed=should_seed)
    desc = "Catalog reset to 6 sample items." if should_seed else "Catalog cleared."
    return {
        "success": True,
        "message": desc,
        "total_items": len(items),
        "items": items
    }
