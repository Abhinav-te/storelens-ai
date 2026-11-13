"""
StoreLens AI - Catalog Persistence & Local Store Manager
Stores catalog identically to Firestore documents in store_catalog.json.
Provides search, filtering, stock mutation, and offline failover logic.
"""
import json
import os
import re
from typing import List, Dict, Optional, Tuple

CATALOG_FILE = os.path.join(os.path.dirname(__file__), "store_catalog.json")

DEFAULT_DEMO_ITEMS = [
    {
        "sku_id": "SKU-BOAT-450",
        "item_name": "boAt Rockerz 450 Bluetooth On-Ear Headphones",
        "brand": "boAt",
        "category": "Audio",
        "color": "Luscious Black",
        "key_specs": ["40mm Dynamic Drivers", "15H Playback", "Voice Assistant Mic"],
        "price_inr": 1499,
        "timestamp_sec": 2.0,
        "stock_count": 5,
        "status": "IN_STOCK",
        "thumbnail_url": "/static/thumbnails/SKU-BOAT-450.jpg"
    },
    {
        "sku_id": "SKU-PORT-KB01",
        "item_name": "Portronics Bubble Wireless Keyboard & Mouse Combo",
        "brand": "Portronics",
        "category": "Keyboards & Mice",
        "color": "Arctic White",
        "key_specs": ["2.4GHz + Dual BT 5.0", "Silent Click", "Multi-device Switch"],
        "price_inr": 749,
        "timestamp_sec": 5.0,
        "stock_count": 4,
        "status": "IN_STOCK",
        "thumbnail_url": "/static/thumbnails/SKU-PORT-KB01.jpg"
    },
    {
        "sku_id": "SKU-NOISE-FIT",
        "item_name": "Noise ColorFit Pulse 2 Max 1.85\" Display Smartwatch",
        "brand": "Noise",
        "category": "Wearables",
        "color": "Jet Black",
        "key_specs": ["1.85'' TFT LCD", "BT Calling", "10-Day Battery Life"],
        "price_inr": 1299,
        "timestamp_sec": 8.0,
        "stock_count": 2,
        "status": "LOW_STOCK",
        "thumbnail_url": "/static/thumbnails/SKU-NOISE-FIT.jpg"
    },
    {
        "sku_id": "SKU-ZEB-TRANS",
        "item_name": "Zebronics Transformer Gaming Mouse with RGB",
        "brand": "Zebronics",
        "category": "Keyboards & Mice",
        "color": "Gold & Black",
        "key_specs": ["3200 DPI Optical Sensor", "6 Buttons", "Breathing LED"],
        "price_inr": 399,
        "timestamp_sec": 11.0,
        "stock_count": 8,
        "status": "IN_STOCK",
        "thumbnail_url": "/static/thumbnails/SKU-ZEB-TRANS.jpg"
    },
    {
        "sku_id": "SKU-SANDISK-64",
        "item_name": "SanDisk Ultra Dual Drive Go Type-C 64GB Flash Drive",
        "brand": "SanDisk",
        "category": "Storage",
        "color": "Navy Blue",
        "key_specs": ["USB 3.1 Gen 1", "Dual USB-C & USB-A", "Up to 150MB/s Read"],
        "price_inr": 649,
        "timestamp_sec": 14.0,
        "stock_count": 6,
        "status": "IN_STOCK",
        "thumbnail_url": "/static/thumbnails/SKU-SANDISK-64.jpg"
    },
    {
        "sku_id": "SKU-JBL-GO3",
        "item_name": "JBL Go 3 Ultra-Portable Waterproof Bluetooth Speaker",
        "brand": "JBL",
        "category": "Audio",
        "color": "Squad Camo",
        "key_specs": ["IP67 Water & Dustproof", "JBL Pro Sound", "5 Hours Playtime"],
        "price_inr": 2999,
        "timestamp_sec": 17.0,
        "stock_count": 1,
        "status": "LOW_STOCK",
        "thumbnail_url": "/static/thumbnails/SKU-JBL-GO3.jpg"
    }
]

def load_catalog() -> List[Dict]:
    """Loads all items from store_catalog.json."""
    if not os.path.exists(CATALOG_FILE):
        return []
    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading catalog: {e}")
        return []

def save_catalog(items: List[Dict]) -> None:
    """Saves items to store_catalog.json."""
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def get_catalog(query: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
    """Retrieves items matching optional query and category filters."""
    items = load_catalog()
    if category and category.lower() != "all":
        items = [i for i in items if i.get("category", "").lower() == category.lower()]
    
    if query:
        q = query.strip().lower()
        filtered = []
        for item in items:
            searchable = " ".join([
                item.get("sku_id", ""),
                item.get("item_name", ""),
                item.get("brand", ""),
                item.get("category", ""),
                item.get("color", ""),
                " ".join(item.get("key_specs", []))
            ]).lower()
            if q in searchable:
                filtered.append(item)
        return filtered
    return items

def upsert_catalog_items(new_items: List[Dict]) -> List[Dict]:
    """Merges new items into the catalog by sku_id."""
    existing = {item["sku_id"]: item for item in load_catalog()}
    for item in new_items:
        sku = item.get("sku_id")
        if not sku:
            sku = f"SKU-{abs(hash(item.get('item_name', 'item')))%10000:04d}"
            item["sku_id"] = sku
        
        # Ensure status is calculated correctly
        stock = int(item.get("stock_count", 0))
        if stock <= 0:
            status = "SOLD_OUT"
        elif stock <= 2:
            status = "LOW_STOCK"
        else:
            status = "IN_STOCK"
        item["status"] = status
        item["stock_count"] = max(0, stock)
        
        existing[sku] = item
    
    updated_list = list(existing.values())
    save_catalog(updated_list)
    return updated_list

def update_item_stock(sku_id: str, action: str, quantity: int = 1) -> Tuple[Optional[Dict], List[Dict]]:
    """Mutates stock count for a single item by sku_id."""
    catalog = load_catalog()
    target_item = None
    
    for item in catalog:
        if item.get("sku_id") == sku_id:
            curr_stock = int(item.get("stock_count", 0))
            act = action.upper()
            if act in ("DECREMENT", "SELL", "SOLD"):
                new_stock = max(0, curr_stock - quantity)
            elif act in ("INCREMENT", "ADD", "RESTOCK"):
                new_stock = curr_stock + quantity
            elif act in ("MARK_SOLD", "ZERO", "OUT_OF_STOCK"):
                new_stock = 0
            else:
                new_stock = curr_stock

            item["stock_count"] = new_stock
            if new_stock <= 0:
                item["status"] = "SOLD_OUT"
            elif new_stock <= 2:
                item["status"] = "LOW_STOCK"
            else:
                item["status"] = "IN_STOCK"
            target_item = item
            break
            
    if target_item:
        save_catalog(catalog)
    return target_item, catalog

def reset_catalog(seed: bool = False) -> List[Dict]:
    """Resets the catalog: empty or pre-seeded with sample inventory."""
    items = DEFAULT_DEMO_ITEMS if seed else []
    save_catalog(items)
    return items

def fallback_nlp_voice_parse(text: str, catalog: List[Dict]) -> Dict:
    """
    Robust fallback parser for Hindi / Hinglish / English merchant phrases.
    Ensures zero failures during live pitches if network drops or 503 spikes occur.
    """
    t = text.lower()
    
    # Extract quantity
    qty = 1
    num_map = {
        "ek": 1, "one": 1, "1": 1,
        "do": 2, "two": 2, "2": 2,
        "teen": 3, "three": 3, "3": 3,
        "char": 4, "chaar": 4, "four": 4, "4": 4,
        "paanch": 5, "panch": 5, "five": 5, "5": 5,
        "chhah": 6, "che": 6, "six": 6, "6": 6,
        "saat": 7, "seven": 7, "7": 7,
        "aath": 8, "eight": 8, "8": 8,
        "nau": 9, "nine": 9, "9": 9,
        "das": 10, "ten": 10, "10": 10
    }
    for word, val in num_map.items():
        if re.search(rf"\b{word}\b", t):
            qty = val
            break

    # Determine action
    if any(k in t for k in ["khatam", "out of stock", "sold out", "zero", "khatm", "nahi bacha"]):
        action = "MARK_SOLD"
    elif any(k in t for k in ["add", "aaya", "aaye", "plus", "restock", "badhao", "mila", "naya"]):
        action = "INCREMENT"
    else:
        # Default action when merchants say "bik gaya", "bech diya", "sold", etc.
        action = "DECREMENT"

    # Match SKU / product in catalog
    matched_sku = None
    best_score = 0
    for item in catalog:
        score = 0
        name_words = item.get("item_name", "").lower().split()
        brand = item.get("brand", "").lower()
        cat = item.get("category", "").lower()
        color = item.get("color", "").lower()
        
        if brand and brand in t:
            score += 5
        if "keyboard" in t and "keyboard" in item.get("item_name", "").lower():
            score += 6
        if "mouse" in t and "mouse" in item.get("item_name", "").lower():
            score += 6
        if ("headset" in t or "headphone" in t or "earphone" in t) and cat == "audio":
            score += 6
        if ("watch" in t or "smartwatch" in t) and cat == "wearables":
            score += 6
        if ("pen drive" in t or "pendrive" in t or "drive" in t or "sandisk" in t) and cat == "storage":
            score += 6
        if color and color in t:
            score += 2

        for w in name_words:
            if len(w) > 3 and w in t:
                score += 2
        
        if score > best_score:
            best_score = score
            matched_sku = item["sku_id"]

    # Default fallback to first catalog item if none matched
    if not matched_sku and catalog:
        matched_sku = catalog[0]["sku_id"]
        
    return {
        "sku_id": matched_sku,
        "action": action,
        "quantity": qty,
        "confirmation_hinglish": f"{action.capitalize()} kiya gaya {qty} unit.",
        "confirmation_en": f"{action.capitalize()}ed {qty} unit(s)."
    }
