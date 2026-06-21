"""Rich fashion recommendation JSON aligned with storefront + taxonomy rules."""

from __future__ import annotations

import hashlib
import os
from typing import Any, Dict, List, Optional

MAIN_ROTATION = [
    "Tops",
    "Bottoms",
    "Footwear",
    "Accessories",
    "Dresses",
    "Outerwear",
    "Activewear",
    "Ethnic Wear",
    "Sleepwear",
    "Innerwear",
    "Swimwear",
]

SUBCATEGORIES: Dict[str, List[str]] = {
    "Tops": ["T-Shirts", "Shirts", "Hoodies", "Sweaters", "Tank Tops", "Crop Tops", "Blazers"],
    "Bottoms": ["Jeans", "Trousers", "Shorts", "Skirts", "Joggers", "Leggings"],
    "Footwear": ["Sneakers", "Formal Shoes", "Boots", "Sandals", "Heels", "Flats"],
    "Accessories": ["Bags", "Watches", "Jewelry", "Belts", "Sunglasses", "Caps"],
    "Dresses": ["Midi Dress", "Maxi Dress", "Mini Dress", "Shirt Dress", "Bodycon"],
    "Outerwear": ["Jackets", "Coats", "Trench", "Bomber", "Parka", "Blazers"],
    "Activewear": ["Sports Bra", "Gym Tee", "Track Pants", "Leggings", "Training Shorts"],
    "Ethnic Wear": ["Kurta", "Saree", "Lehenga", "Sherwani", "Dupatta"],
    "Sleepwear": ["Pajama Set", "Nightdress", "Robe", "Lounge Shorts"],
    "Innerwear": ["Briefs", "Bras", "Vests", "Thermals"],
    "Swimwear": ["Swimsuit", "Bikini", "Swim Shorts", "Cover-Up"],
}

STYLE_CATEGORIES = [
    "Casual",
    "Formal",
    "Streetwear",
    "Minimalist",
    "Vintage",
    "Bohemian",
    "Athleisure",
    "Partywear",
    "Smart Casual",
    "Business Casual",
    "Traditional",
    "Luxury",
]

OCCASIONS = [
    "Office",
    "Wedding",
    "Party",
    "Gym",
    "Travel",
    "Date Night",
    "College",
    "Vacation",
    "Festival",
    "Daily Wear",
]

SEASONS = ["Summer", "Winter", "Monsoon", "Spring", "Autumn", "All Season"]

COLORS = [
    "Black",
    "White",
    "Blue",
    "Red",
    "Green",
    "Beige",
    "Brown",
    "Grey",
    "Pink",
    "Yellow",
    "Pastel",
    "Neon",
    "Earth Tone",
]

FIT_TYPES = ["Slim Fit", "Regular Fit", "Oversized", "Relaxed Fit", "Skinny Fit"]

FABRICS = ["Cotton", "Denim", "Linen", "Wool", "Polyester", "Silk", "Leather"]

GENDERS = ["Men", "Women", "Unisex", "Kids"]


def _seed(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)


def _pick(seed: str, options: List[str]) -> str:
    return options[_seed(seed) % len(options)]


def absolute_image_url(image: str, product_id: str) -> str:
    img = str(image or "").strip()
    if not img:
        return f"https://picsum.photos/seed/outfit-{_seed(product_id) % 10_000}/640/760"
    if img.startswith("http"):
        return img
    base = os.getenv("PUBLIC_API_BASE", "http://127.0.0.1:8000").rstrip("/")
    return f"{base}{img}" if img.startswith("/") else f"{base}/{img}"


def _nearest_style(user_styles: List[str], fallback: str) -> str:
    if not user_styles:
        return _pick(fallback, STYLE_CATEGORIES)
    low = [s.lower() for s in STYLE_CATEGORIES]
    for u in user_styles:
        ulow = u.lower()
        for sc in STYLE_CATEGORIES:
            if ulow in sc.lower() or sc.lower() in ulow:
                return sc
        for i, l in enumerate(low):
            if ulow in l or l in ulow:
                return STYLE_CATEGORIES[i]
    return _pick(user_styles[0], STYLE_CATEGORIES)


def _occasion(profile: Dict[str, Any], hint: Optional[str]) -> str:
    if hint and str(hint).strip():
        t = str(hint).strip().title()
        for o in OCCASIONS:
            if o.lower() == t.lower():
                return o
        return t
    o = profile.get("preferred_occasion") or profile.get("occasion")
    if isinstance(o, str) and o.strip():
        return o.strip().title()
    return _pick(str(profile.get("name", "user")), OCCASIONS)


def _season(hint: Optional[str], product_id: str) -> str:
    if hint and hint.strip():
        for s in SEASONS:
            if s.lower() == hint.lower().strip():
                return s
        return _pick(hint, SEASONS)
    return _pick(product_id, SEASONS)


def _gender(profile: Dict[str, Any], hint: Optional[str]) -> str:
    if hint and hint.strip():
        for g in GENDERS:
            if g.lower() == hint.lower().strip():
                return g
        return _pick(hint, GENDERS)
    g = profile.get("gender")
    if isinstance(g, str) and g.strip():
        for opt in GENDERS:
            if opt.lower() == g.strip().lower():
                return opt
    return "Unisex"


def _product_reason(
    main_cat: str,
    style: str,
    color: str,
    occasion: str,
    season: str,
    pref_styles: List[str],
    pref_colors: List[str],
) -> str:
    bits = [
        f"Curated for {occasion} in {season}.",
        f"{main_cat} in {color} suits a {style} direction.",
    ]
    if pref_styles:
        bits.append(f"Echoes your interest in {pref_styles[0]}.")
    if pref_colors:
        bits.append(f"Works with palettes featuring {pref_colors[0]}.")
    bits.append("Picked for visual balance with trending, highly rated picks.")
    return " ".join(bits)


def build_engine_response(
    recommendations: List[Any],
    products_by_id: Dict[str, Dict[str, Any]],
    profile: Dict[str, Any],
    occasion_hint: Optional[str] = None,
    season_hint: Optional[str] = None,
    gender_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Build ``recommended_products`` + ``outfit_recommendation`` (+ legacy ``items``)."""
    pref_styles = profile.get("preferred_styles") or []
    if not isinstance(pref_styles, list):
        pref_styles = []
    pref_colors = profile.get("preferred_colors") or []
    if not isinstance(pref_colors, list):
        pref_colors = []

    if not recommendations:
        empty_slot = {"product_name": "", "image_url": ""}
        return {
            "recommended_products": [],
            "outfit_recommendation": {
                "top": empty_slot,
                "bottom": empty_slot,
                "footwear": empty_slot,
                "accessory": empty_slot,
                "style_match_reason": "No scored items for the current filters; widen filters or update preferences.",
            },
            "items": [],
            "meta": {"gender": _gender(profile, gender_hint), "occasion": _occasion(profile, occasion_hint)},
        }

    occasion = _occasion(profile, occasion_hint)
    gender = _gender(profile, gender_hint)

    recommended_products: List[Dict[str, str]] = []
    for i, rec in enumerate(recommendations):
        pid = str(rec.item_id)
        catalog = products_by_id.get(pid, {})
        name = str(catalog.get("name") or "Suggested item")
        brand = str(catalog.get("brand") or "FashionHub")
        raw_img = str(catalog.get("image") or rec.image or "")
        image_url = absolute_image_url(raw_img, pid)
        color = str(catalog.get("color") or rec.color or _pick(pid + "c", COLORS))
        style = _nearest_style(pref_styles, str(rec.style or "Casual"))
        main_cat = MAIN_ROTATION[i % len(MAIN_ROTATION)]
        sub = _pick(pid + main_cat, SUBCATEGORIES.get(main_cat, ["General"]))
        material = _pick(pid + "m", FABRICS)
        fit = _pick(pid + "f", FIT_TYPES)
        season = _season(season_hint, pid + str(i))
        price_val = catalog.get("price")
        if price_val is None:
            price_val = round(599 + (_seed(pid) % 2800) / 10, 2)
        rating_val = catalog.get("rating")
        if rating_val is None:
            rating_val = round(3.8 + (_seed(pid + "r") % 12) / 10, 1)
        reason = _product_reason(main_cat, style, color, occasion, season, pref_styles, pref_colors)

        recommended_products.append(
            {
                "product_id": pid,
                "product_name": name,
                "brand": brand,
                "image_url": image_url,
                "category": main_cat,
                "subcategory": sub,
                "style": style,
                "occasion": occasion,
                "season": season,
                "color": color,
                "material": material,
                "fit": fit,
                "price": str(price_val),
                "rating": str(rating_val),
                "reason": reason,
            }
        )

    def slot(main: str) -> Dict[str, str]:
        for p in recommended_products:
            if p["category"] == main:
                return {"product_name": p["product_name"], "image_url": p["image_url"]}
        return {"product_name": "", "image_url": ""}

    top = slot("Tops")
    bottom = slot("Bottoms")
    foot = slot("Footwear")
    acc = slot("Accessories")
    if not top["product_name"]:
        top = {"product_name": recommended_products[0]["product_name"], "image_url": recommended_products[0]["image_url"]}
    if not bottom["product_name"] and len(recommended_products) > 1:
        bottom = {
            "product_name": recommended_products[1]["product_name"],
            "image_url": recommended_products[1]["image_url"],
        }
    if not foot["product_name"]:
        for p in recommended_products:
            if p["category"] == "Footwear":
                foot = {"product_name": p["product_name"], "image_url": p["image_url"]}
                break
        if not foot["product_name"] and len(recommended_products) > 2:
            foot = {
                "product_name": recommended_products[2]["product_name"],
                "image_url": recommended_products[2]["image_url"],
            }
    if not acc["product_name"]:
        for p in recommended_products:
            if p["category"] == "Accessories":
                acc = {"product_name": p["product_name"], "image_url": p["image_url"]}
                break
        if not acc["product_name"] and len(recommended_products) > 3:
            acc = {
                "product_name": recommended_products[3]["product_name"],
                "image_url": recommended_products[3]["image_url"],
            }

    anchor = recommended_products[0]["color"] if recommended_products else "neutral"
    style_match = (
        f"Coordinated {gender} look for {occasion}: anchors on {anchor} tones, "
        f"{recommended_products[0]['style'] if recommended_products else 'Casual'} styling, "
        "and pieces chosen to avoid clashing silhouettes."
    )

    outfit_recommendation = {
        "top": top,
        "bottom": bottom,
        "footwear": foot,
        "accessory": acc,
        "style_match_reason": style_match,
    }

    items = [
        {
            "item_id": r.item_id,
            "image": absolute_image_url(str(getattr(r, "image", "") or ""), str(r.item_id)),
            "category": r.category,
            "color": r.color,
            "style": r.style,
            "score": r.score,
            "reason": r.reason,
            "tags": r.tags,
        }
        for r in recommendations
    ]

    return {
        "recommended_products": recommended_products,
        "outfit_recommendation": outfit_recommendation,
        "items": items,
        "meta": {"gender": gender, "occasion": occasion},
    }
