"""
StoreLens AI - Gemini Multimodal Intelligence Service
Interfaces with the official google-genai SDK (gemini-3.8-flash)
for video shelf cataloging and merchant voice inventory updates.
"""
import os
import sys
import re
import json
import time
from typing import List, Dict, Optional, Any

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from google import genai
from google.genai import types

from catalog import load_catalog, DEFAULT_DEMO_ITEMS, fallback_nlp_voice_parse

# Never overwrite existing shell environment variables
load_dotenv(override=False)

def extract_key_from_shell_profiles() -> Optional[str]:
    """Inspects shell profile files for an exported GEMINI_API_KEY if not in subshell env."""
    profile_paths = [
        os.path.expanduser("~/.bashrc"),
        os.path.expanduser("~/.profile"),
        os.path.expanduser("~/.bash_profile"),
        os.path.expanduser("~/.zshrc"),
    ]
    pattern = re.compile(r'^\s*(?:export\s+)?GEMINI_API_KEY=["\']?([^"\']+)["\']?', re.MULTILINE)
    for p in profile_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                m = pattern.search(content)
                if m:
                    return m.group(1).strip()
            except Exception:
                pass
    return None

def get_api_keys() -> List[str]:
    """
    Extracts API keys from GEMINI_API_KEY environment variable.
    Unconditionally filters out any token starting with 'AQ.' so they are never sent to genai.Client.
    If GEMINI_API_KEY is empty in os.environ, checks ~/.bashrc and ~/.profile.
    """
    raw = os.environ.get("GEMINI_API_KEY", "")
    if not raw:
        profile_key = extract_key_from_shell_profiles()
        if profile_key:
            raw = profile_key

    all_keys = [k.strip() for k in raw.split(",") if k.strip()]
    # Unconditionally filter out any token starting with AQ.
    valid_keys = [k for k in all_keys if not k.startswith("AQ.")]
    return valid_keys

def get_client(key_idx: int = 0) -> Optional[genai.Client]:
    """Returns a google-genai Client instance with rotating key selection."""
    keys = get_api_keys()
    if not keys:
        return None
    key = keys[key_idx % len(keys)]
    return genai.Client(api_key=key)

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.1-flash-lite"]

def call_gemini_with_fallback(
    contents: Any,
    system_instruction: Optional[str] = None,
    json_mode: bool = True
) -> Optional[str]:
    """
    Executes a prompt against gemini-3.8-flash with automatic model cascades
    and multi-key rotation inside the retry loop.
    """
    keys = get_api_keys()
    if not keys:
        print("[GeminiService] No GEMINI_API_KEY configured in environment.")
        return None

    config_kwargs = {}
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction

    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    # Rotate through models and rotate keys on each attempt
    all_models = [PRIMARY_MODEL] + FALLBACK_MODELS
    last_error = None
    for model_name in all_models:
        for attempt in range(max(2, len(keys))):
            client = get_client(attempt)
            if not client:
                continue
            try:
                print(f"[GeminiService] Calling model '{model_name}' (key index {attempt % len(keys)})...")
                res = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                if res and res.text:
                    print(f"[GeminiService] Model '{model_name}' responded successfully.")
                    return res.text
            except Exception as e:
                last_error = e
                print(f"[GeminiService] Model '{model_name}' failed with key {attempt % len(keys)}: {e}")
                time.sleep(1)

    print(f"[GeminiService] All model and key attempts exhausted. Last error: {last_error}")
    return None

def analyze_video_walkthrough(video_path: str, use_sample: bool = False) -> List[Dict]:
    """
    Uploads shelf walkthrough video, prompts Gemini 3.8 Flash to extract
    every visible retail product, matching spoken Hindi/Hinglish/English prices by timestamp.
    
    If use_sample is False (real user video), failures will NOT inject fake demo items.
    """
    client = get_client(0)
    if not client:
        if use_sample:
            return DEFAULT_DEMO_ITEMS
        raise RuntimeError("GEMINI_API_KEY is not configured or invalid.")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    uploaded_file = None
    try:
        print(f"[GeminiService] Uploading video to Gemini File API: {video_path}")
        uploaded_file = client.files.upload(file=video_path)
        
        # Wait for file processing to complete
        for _ in range(20):
            file_status = client.files.get(name=uploaded_file.name)
            print(f"[GeminiService] File state: {file_status.state}")
            if file_status.state == "ACTIVE":
                break
            time.sleep(1.5)
    except Exception as e:
        print(f"[GeminiService] File upload error: {e}")
        if not use_sample:
            raise RuntimeError(f"Failed to upload video to Gemini File API: {str(e)}")

    prompt = """
    You are StoreLens AI, an expert retail computer vision engine.
    Carefully inspect this store shelf walkthrough video and its accompanying audio track.
    
    Critical Instructions:
    1. Optical Character Recognition (OCR):
       - Accurately read stylized packaging fonts, graffiti logos, bold gaming typography, and small model numbers printed on retail boxes.
       - Do not approximate or invent generic brands; read exact names visible on the packaging (e.g. 'Dawg Headbug G60', 'Portronics Hydra 10', 'Redmi K50i', 'boAt Rockerz 450', 'Noise ColorFit Pulse 2').
    2. Spoken Price Synchronization:
       - Strictly listen to the merchant speaking prices in Hindi, Hinglish, or English (e.g. 'pandrah sau' = 1500, 'saat sau pachas' = 750, 'do hazaar' = 2000, 'three hundred' = 300).
       - Match each spoken price strictly to the item centered and in focus at that exact video timestamp. If no price is spoken, estimate standard retail price in INR (integer).
    3. Precise Timestamps:
       - Note the exact timestamp_sec (float) when each product is most clearly visible, centered, and unobstructed on the shelf.
    4. Specifications & Output Format:
       - Return key_specs strictly as a JSON array of strings (e.g. ["Bluetooth 5.3", "50ms Low Latency", "40H Battery"]). Do NOT return a string or nested object.
       - Return standard retail category (Audio, Keyboards & Mice, Wearables, Storage, Mobile Accessories, Electronics).
       - Return visible color and shelf stock count (integer).

    Return a STRICT JSON array of objects conforming to this schema:
    [
      {
        "sku_id": "SKU-PROD-01",
        "item_name": "Full Exact Product Name",
        "brand": "Brand",
        "category": "Audio",
        "color": "Black",
        "key_specs": ["Spec 1", "Spec 2", "Spec 3"],
        "price_inr": 1499,
        "timestamp_sec": 2.5,
        "stock_count": 5,
        "status": "IN_STOCK"
      }
    ]
    """

    contents = [uploaded_file, prompt] if uploaded_file else prompt
    gemini_output = call_gemini_with_fallback(contents, json_mode=True)

    if gemini_output:
        try:
            clean_json = gemini_output.strip()
            if clean_json.startswith("```"):
                clean_json = clean_json.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            parsed = json.loads(clean_json)
            
            raw_items = []
            if isinstance(parsed, list) and len(parsed) > 0:
                raw_items = parsed
            elif isinstance(parsed, dict) and "items" in parsed:
                raw_items = parsed["items"]

            if raw_items:
                # Sanitize and guarantee key_specs is list[str]
                for item in raw_items:
                    specs = item.get("key_specs")
                    if isinstance(specs, str):
                        item["key_specs"] = [s.strip() for s in specs.split(",") if s.strip()]
                    elif not isinstance(specs, list):
                        item["key_specs"] = []
                    else:
                        item["key_specs"] = [str(s) for s in specs]
                print(f"[GeminiService] Extracted {len(raw_items)} items from video via Gemini.")
                return raw_items
        except Exception as e:
            print(f"[GeminiService] JSON parse error on Gemini output: {e}")
            if not use_sample:
                raise RuntimeError(f"Failed to parse Gemini video analysis output: {str(e)}")

    if use_sample:
        print("[GeminiService] Using pre-recorded demo items for sample walkthrough.")
        return DEFAULT_DEMO_ITEMS
    
    raise RuntimeError("Gemini failed to extract retail products from the uploaded video. Check API quota, demand status, or video format.")

def analyze_voice_command(
    audio_path: Optional[str] = None,
    transcript: Optional[str] = None,
    current_catalog: Optional[List[Dict]] = None
) -> Dict:
    """
    Parses a merchant voice note via gemini-3.8-flash using fast inline audio bytes.
    Matches sku_id, action, and quantity against active store inventory.
    """
    if current_catalog is None:
        current_catalog = load_catalog()

    catalog_context = [
        {
            "sku_id": item["sku_id"],
            "name": item["item_name"],
            "brand": item["brand"],
            "category": item["category"],
            "color": item.get("color", ""),
            "stock_count": item["stock_count"],
            "price_inr": item["price_inr"]
        }
        for item in current_catalog
    ]

    # Convert audio file directly to fast inline bytes
    audio_part = None
    if audio_path and os.path.exists(audio_path):
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            
            ext = os.path.splitext(audio_path)[1].lower()
            if ext in (".webm", ".weba"):
                mime_type = "audio/webm"
            elif ext in (".wav",):
                mime_type = "audio/wav"
            elif ext in (".mp3",):
                mime_type = "audio/mp3"
            elif ext in (".m4a", ".aac"):
                mime_type = "audio/mp4"
            elif ext in (".ogg",):
                mime_type = "audio/ogg"
            else:
                mime_type = "audio/webm"

            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            print(f"[GeminiService] Prepared inline audio bytes ({len(audio_bytes)} bytes, {mime_type}).")
        except Exception as e:
            print(f"[GeminiService] Inline audio conversion error: {e}")

    system_instruction = (
        "You are StoreLens AI inventory manager. "
        "Listen to merchant voice instructions spoken in Hindi, Hinglish, or English "
        "(e.g., 'Ek Portronics keyboard bik gaya', '2 black headsets sold', 'Noise smartwatch out of stock'). "
        "Match the merchant's intent strictly against the provided catalog items. "
        "Output strictly valid JSON with keys: 'sku_id', 'action' ('DECREMENT' | 'INCREMENT' | 'MARK_SOLD'), "
        "'quantity' (integer, default 1), 'confirmation_hinglish' (neutral confirmation message without emojis), "
        "and 'confirmation_en' (clean factual English message without emojis)."
    )

    prompt = f"""
    Current Store Catalog Inventory:
    {json.dumps(catalog_context, indent=2)}

    Merchant voice transcript / instruction:
    "{transcript or 'Analyze the attached inline audio speech directly.'}"

    Identify:
    1. Target sku_id from the catalog that best matches the spoken product.
    2. Action: DECREMENT (sold, bik gaya, bech diya), INCREMENT (restocked, aaya, add), or MARK_SOLD (out of stock, khatam).
    3. Quantity: number of units (e.g. 'ek' -> 1, 'do' -> 2, 'teen' -> 3). Default is 1.
    4. confirmation_hinglish: Factual confirmation message in Hinglish without emojis.
    5. confirmation_en: Clean factual English message without emojis.
    """

    contents = [audio_part, prompt] if audio_part else prompt
    gemini_output = call_gemini_with_fallback(
        contents=contents,
        system_instruction=system_instruction,
        json_mode=True
    )

    if gemini_output:
        try:
            clean_json = gemini_output.strip()
            if clean_json.startswith("```"):
                clean_json = clean_json.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            result = json.loads(clean_json)
            if "sku_id" in result and "action" in result:
                # Strip any accidental emojis in confirmation strings
                for k in ["confirmation_hinglish", "confirmation_en"]:
                    if k in result and isinstance(result[k], str):
                        result[k] = result[k].replace("✅", "").replace("🎙️", "").strip()
                return result
        except Exception as e:
            print(f"[GeminiService] Voice output parse error: {e}")

    # Fallback to local NLP parser
    text_to_parse = transcript or "1 item sold"
    print(f"[GeminiService] Falling back to local Hinglish NLP parser for: '{text_to_parse}'")
    return fallback_nlp_voice_parse(text_to_parse, current_catalog)
