"""Retail-style product names and curated hero images for catalog items."""

from __future__ import annotations

import hashlib
import re
from typing import List

# Unsplash hotlinks (allowed); fashion / beauty / lifestyle–adjacent crops.
_I = "w=640&h=800&fit=crop&q=86&auto=format"
_CLOTHING_IMG: List[str] = [
    f"https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?{_I}",
    f"https://images.unsplash.com/photo-1434389677669-e08b4cac310c?{_I}",
    f"https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?{_I}",
    f"https://images.unsplash.com/photo-1490114538077-0a7f8cb49891?{_I}",
    f"https://images.unsplash.com/photo-1469334031218-e382a71b716b?{_I}",
    f"https://images.unsplash.com/photo-1485968579580-b6d095142e6e?{_I}",
    f"https://images.unsplash.com/photo-1551028719-00167b16eac5?{_I}",
    f"https://images.unsplash.com/photo-1509631179647-017733169c12?{_I}",
]
_FOOTWEAR_IMG: List[str] = [
    f"https://images.unsplash.com/photo-1543163521-1bf539c55dd2?{_I}",
    f"https://images.unsplash.com/photo-1560769629-975ec94e6a86?{_I}",
    f"https://images.unsplash.com/photo-1549298916-b41d501d3772?{_I}",
    f"https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?{_I}",
    f"https://images.unsplash.com/photo-1600185365928-3a27e7ae57f5?{_I}",
    f"https://images.unsplash.com/photo-1606107557195-0e29a258bfe4?{_I}",
]
_MAKEUP_IMG: List[str] = [
    f"https://images.unsplash.com/photo-1515377905703-c4788e51af15?{_I}",
    f"https://images.unsplash.com/photo-1596462502278-27bfdc403348?{_I}",
    f"https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?{_I}",
    f"https://images.unsplash.com/photo-1631214524020-7e9641339c74?{_I}",
    f"https://images.unsplash.com/photo-1620916566398-39f1143ab7be?{_I}",
]
_DAILY_IMG: List[str] = [
    f"https://images.unsplash.com/photo-1584917865442-de89df76afd3?{_I}",
    f"https://images.unsplash.com/photo-1553062407-98eeb64c6a62?{_I}",
    f"https://images.unsplash.com/photo-1523275335684-37898b6baf30?{_I}",
    f"https://images.unsplash.com/photo-1524592094714-0f0654e20314?{_I}",
    f"https://images.unsplash.com/photo-1524805444758-089113d48a6d?{_I}",
]
_HOME_IMG: List[str] = [
    f"https://images.unsplash.com/photo-1586023492125-27b2c045efd7?{_I}",
    f"https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?{_I}",
    f"https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?{_I}",
    f"https://images.unsplash.com/photo-1555041469-a586c61ea9bc?{_I}",
    f"https://images.unsplash.com/photo-1503602642458-232111445657?{_I}",
]

_NAME_CLOTHING = [
    "Cotton Tee",
    "Slim Jeans",
    "Knit Sweater",
    "Casual Shirt",
    "Midi Dress",
    "Denim Jacket",
    "Hoodie",
    "Chino Pants",
    "Summer Shorts",
    "Blazer",
    "A-Line Skirt",
    "Polo Shirt",
]
_NAME_FOOTWEAR = [
    "Sneakers",
    "Loafers",
    "Ankle Boots",
    "Sandals",
    "Running Shoes",
    "Oxfords",
    "Slip-Ons",
    "Trainers",
]
_NAME_MAKEUP = [
    "Lipstick",
    "Foundation",
    "Face Powder",
    "Brow Pencil",
    "Highlighter",
    "Mascara",
    "Blush",
    "Eye Primer",
]
_NAME_DAILY = [
    "Crossbody Bag",
    "Wallet",
    "Sunglasses",
    "Tote Bag",
    "Watch",
    "Leather Belt",
    "Water Bottle",
    "Umbrella",
]
_NAME_HOME = [
    "Cushion Set",
    "Table Lamp",
    "Serving Board",
    "Bath Towels",
    "Candle Set",
    "Storage Baskets",
    "Mug Set",
    "Cotton Throw",
]


def _stable_index(key: str, n: int) -> int:
    if n <= 0:
        return 0
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % n


def _extend_pool(pool: List[str], target_len: int) -> List[str]:
    """Cycle images so every name slot has a matching image index (paired hero + title)."""
    if target_len <= 0:
        return []
    if not pool:
        return []
    if len(pool) >= target_len:
        return pool[:target_len]
    out = list(pool)
    while len(out) < target_len:
        out.append(pool[len(out) % len(pool)])
    return out


_NAME_POOLS = {
    "Clothing Items": _NAME_CLOTHING,
    "Footwear": _NAME_FOOTWEAR,
    "Makeup Products": _NAME_MAKEUP,
    "Daily Use Products": _NAME_DAILY,
    "Home Products": _NAME_HOME,
}

_IMG_POOLS = {
    "Clothing Items": _CLOTHING_IMG,
    "Footwear": _FOOTWEAR_IMG,
    "Makeup Products": _MAKEUP_IMG,
    "Daily Use Products": _DAILY_IMG,
    "Home Products": _HOME_IMG,
}


def _catalog_name_image_bundle(category: str, product_id: str, row_index: int) -> tuple[list[str], list[str], int]:
    """Shared slot for title + image so the hero photo matches the product line (same index into paired pools)."""
    key = f"{product_id}:{row_index}"
    names = _NAME_POOLS.get(category) or _NAME_CLOTHING
    imgs_raw = _IMG_POOLS.get(category) or _CLOTHING_IMG
    imgs = _extend_pool(imgs_raw, len(names))
    slot = _stable_index(key, len(names))
    return names, imgs, slot


def display_color(raw: str) -> str:
    """Short, title-case color label from messy CSV text."""
    s = re.sub(r"\s+", " ", (raw or "").strip())
    if not s:
        return "Ivory"
    if "," in s:
        s = s.split(",")[0].strip()
    s = re.sub(r"^earth tones[, ]*", "", s, flags=re.I)
    if len(s) > 36:
        s = s[:35].rstrip(" ,;") + "…"
    return s.title()


def short_color_name(raw: str) -> str:
    """One or two words for product titles (keeps names readable)."""
    s = re.sub(r"\s+", " ", (raw or "").strip())
    if not s:
        return "Neutral"
    if "," in s:
        s = s.split(",")[0].strip()
    s = re.sub(r"^earth tones[, ]*", "", s, flags=re.I)
    words = s.split()[:2]
    out = " ".join(words).title()
    if len(out) > 20:
        out = out[:18].rstrip() + "…"
    return out or "Neutral"


def short_style_label(raw: str, max_len: int = 36) -> str:
    """Short label from CSV style columns (avoids long phrases on cards and filters)."""
    s = re.sub(r"\s+", " ", (raw or "").strip()).title()
    if not s:
        return "Classic"
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def catalog_image_url(category: str, product_id: str, row_index: int) -> str:
    _, imgs, slot = _catalog_name_image_bundle(category, product_id, row_index)
    return imgs[slot]


def catalog_product_name(
    category: str,
    _style_raw: str,
    color_raw: str,
    _brand: str,
    product_id: str,
    row_index: int,
) -> str:
    names, _, slot = _catalog_name_image_bundle(category, product_id, row_index)
    color = short_color_name(color_raw)
    return f"{names[slot]}, {color}"


def catalog_description(category: str, color_raw: str, style_raw: str, brand: str) -> str:
    del style_raw
    color = short_color_name(color_raw)
    if category == "Home Products":
        return f"{brand} home piece with {color} tones. Fits everyday spaces."
    if category == "Makeup Products":
        return f"{brand} makeup for {color} looks. Easy to blend and wear."
    if category == "Daily Use Products":
        return f"{brand} everyday essential with {color} accents. Compact and durable."
    if category == "Footwear":
        return f"{brand} shoes in a {color} palette. Comfortable for daily wear."
    return f"{brand} {category.replace(' Items', '').lower()}: {color} palette, easy to style."
