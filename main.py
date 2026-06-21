import os
import uuid
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import razorpay
import stripe
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .auth import create_access_token, hash_password, require_admin, verify_password
from .db import init_db
from . import models  # noqa: F401
from .catalog_enrichment import (
    catalog_description,
    catalog_image_url,
    catalog_product_name,
    short_color_name,
    short_style_label,
)
from .recommendation_output import build_engine_response
from .recommender import DeepFashionRecommender
from .schemas import (
    AdminProductUpsertRequest,
    CartItemRequest,
    CartRemoveRequest,
    CartUpdateRequest,
    CheckoutRequest,
    ForgotPasswordRequest,
    RecommendRequest,
    RazorpayOrderRequest,
    ReviewCreateRequest,
    SaveItemRequest,
    StripePaymentIntentRequest,
    UpdateProfileRequest,
    UserLogin,
    UserSignup,
)
from .storage import (
    add_or_update_cart_item,
    add_review,
    clear_cart,
    create_order,
    create_password_reset,
    create_user,
    get_all_orders,
    get_all_users,
    get_cart,
    get_orders_for_user,
    get_reviews_for_product,
    get_saved_for_user,
    get_user_by_email,
    get_user_by_id,
    remove_cart_item,
    remove_saved_item_for_user,
    save_item_for_user,
    update_user,
    migrate_json_to_postgres,
)

app = FastAPI(title="Fashion Recommender API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

root = Path(__file__).resolve().parents[1]
dataset_csv = Path(os.getenv("FASHION_DATASET_CSV", root / "data" / "fashion.csv"))
image_root = Path(os.getenv("FASHION_IMAGE_ROOT", root / "data" / "images"))
model = DeepFashionRecommender(dataset_csv=dataset_csv, image_root=image_root)
if image_root.exists():
    app.mount("/images", StaticFiles(directory=image_root), name="images")

PRODUCTS: list[Dict[str, Any]] = []
VERIFIED_PAYMENTS: set[str] = set()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
razorpay_client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", "")))


def _as_url_image(value: str, row_index: int) -> str:
    image = str(value or "").strip()
    if image.startswith("http"):
        return image
    if image:
        return f"/images/{image.replace(os.sep, '/')}"
    return f"https://picsum.photos/seed/fashion-{row_index}/640/760"


def _safe_float(raw: Any, fallback: float) -> float:
    try:
        value = float(raw)
        if value != value:
            return fallback
        return value
    except Exception:
        return fallback


def _resolve_col(columns: list[str], keywords: list[str], fallback: str) -> str:
    lowered = {c.lower(): c for c in columns}
    for keyword in keywords:
        for low, original in lowered.items():
            if keyword in low:
                return original
    return fallback


# Storefront categories (shown in /categories, filters, product cards).
CATALOG_CATEGORIES = [
    "Clothing Items",
    "Footwear",
    "Makeup Products",
    "Daily Use Products",
    "Home Products",
]


def _map_catalog_category(row: pd.Series, row_index: int) -> str:
    """
    Map a CSV row to one of CATALOG_CATEGORIES. Strong keyword matches win;
    otherwise rows cycle so every category appears in the catalog.
    """
    blob = " ".join(str(v).lower() for v in row.values)

    if any(
        k in blob
        for k in (
            "makeup",
            "lipstick",
            "lip gloss",
            "foundation",
            "mascara",
            "eyeliner",
            "blush",
            "concealer",
            "kajal",
            "cosmetic",
        )
    ):
        return "Makeup Products"
    if any(
        k in blob
        for k in (
            "kitchen",
            "bedding",
            "decor",
            "cushion",
            "tableware",
            "serveware",
            "lamp",
            "curtain",
            "storage box",
            "dinnerware",
            "cookware",
        )
    ):
        return "Home Products"
    if any(
        k in blob
        for k in (
            "wallet",
            "wristwatch",
            "watch band",
            "umbrella",
            "towel",
            "backpack",
            "handbag",
            "tote bag",
            "water bottle",
            "charger",
            "notebook",
            "hair clip",
            "scrunch",
            "hair band",
            "hair pin",
        )
    ):
        return "Daily Use Products"

    shoes_col = next((c for c in row.index if "shoe" in str(c).lower()), None)
    if shoes_col:
        st = str(row.get(shoes_col, "")).lower()
        if any(
            k in st
            for k in (
                "sneaker",
                "boot",
                "loafer",
                "sport shoe",
                "running shoe",
                "sandals",
                "oxford",
                "mule",
            )
        ):
            return "Footwear"
        # "heels" / platforms only (avoid classifying every "low heels or flats" row as footwear-only mix)
        if "platform" in st or ("heel" in st and "wedge" in st):
            return "Footwear"

    return CATALOG_CATEGORIES[row_index % len(CATALOG_CATEGORIES)]


def _catalog_sale_price_inr(category: str, row_index: int) -> float:
    """Round INR shelf prices by category (CSV has no reliable price column)."""
    tiers = {
        "Clothing Items": [499, 699, 899, 1099, 1299, 1499, 1799, 1999, 2199, 2499],
        "Footwear": [899, 1199, 1499, 1799, 2199, 2599, 2999, 3499, 3999, 4499],
        "Makeup Products": [199, 249, 299, 399, 499, 599, 799, 999, 1199, 1499],
        "Daily Use Products": [299, 449, 599, 749, 899, 1099, 1299, 1599, 1899, 2199],
        "Home Products": [399, 599, 799, 999, 1299, 1599, 1899, 2299, 2799, 3299],
    }
    prices = tiers.get(category, [599, 899, 1299, 1599, 1999, 2299])
    return float(prices[row_index % len(prices)])


def _build_product_catalog() -> list[Dict[str, Any]]:
    if not dataset_csv.exists():
        return []
    df = pd.read_csv(dataset_csv).fillna("")
    if df.empty:
        return []
    columns = list(df.columns)
    color_col = _resolve_col(columns, ["color"], columns[min(2, len(columns) - 1)])
    style_col = _resolve_col(columns, ["style", "pattern", "fabric"], columns[min(3, len(columns) - 1)])
    # Do not fall back to the last column: many CSVs have no image column and would
    # mis-map unrelated text (e.g. "Do Exaggerate") to broken /images/... URLs.
    image_col = _resolve_col(columns, ["image", "img", "file"], "")
    brands = ["StyleNest", "UrbanGlow", "VogueCraft", "MeadowWear", "FrostBerry", "IndigoLane", "CoralCharm", "Trendora"]
    products: list[Dict[str, Any]] = []
    max_rows = min(len(df), 1200)
    for i in range(max_rows):
        row = df.iloc[i]
        category = _map_catalog_category(row, i)
        color_raw = str(row.get(color_col, "") or "Neutral")
        style_raw = str(row.get(style_col, "") or "Modern")
        style = short_style_label(style_raw)
        color = short_color_name(color_raw)
        brand = brands[i % len(brands)]
        price = _catalog_sale_price_inr(category, i)
        rating = round(3.6 + (i % 14) / 10, 1)
        if rating > 5:
            rating = 4.9
        discount = [5, 10, 15, 20, 25][i % 5]
        # Canonical storefront ID: one CSV row ≡ one product (matches recommender row index).
        pid = f"p-{i}"
        name = catalog_product_name(category, style_raw, color_raw, brand, pid, i)
        csv_img = str(row.get(image_col, "")).strip() if image_col else ""
        image = _as_url_image(csv_img, i) if csv_img else catalog_image_url(category, pid, i)
        products.append(
            {
                "id": pid,
                "name": name,
                "category": category,
                "brand": brand,
                "price": price,
                "original_price": round(price + price * discount / 100, 2),
                "discount_percent": discount,
                "rating": rating,
                "reviews_count": 14 + (i % 320),
                "color": color,
                "style": style,
                "description": catalog_description(category, color_raw, style_raw, brand),
                "image": image,
                "stock": 5 + (i % 40),
                "tags": [category, color, style],
            }
        )
    return products


def _find_product(product_id: str) -> Dict[str, Any] | None:
    for product in PRODUCTS:
        if str(product["id"]) == str(product_id):
            return product
    return None


def _ensure_demo_accounts() -> None:
    demo_accounts = [
        ("admin@fashionhub.com", "Admin@123", {"name": "Demo Admin", "preferred_styles": [], "preferred_colors": []}),
        ("user@fashionhub.com", "User@123", {"name": "Demo User", "preferred_styles": [], "preferred_colors": []}),
    ]
    for email, password, profile in demo_accounts:
        existing = get_user_by_email(email)
        if existing:
            continue
        create_user(email=email, password_hash=hash_password(password), profile=profile)


@app.on_event("startup")
def startup() -> None:
    global PRODUCTS
    init_db()
    migration_counts = migrate_json_to_postgres()
    if any(migration_counts.values()):
        print(f"[INFO] Migrated JSON data to PostgreSQL: {migration_counts}")
    if dataset_csv.exists():
        model.prepare()
        print("[INFO] Fashion recommender prepared.")
    else:
        print(f"[WARN] Dataset not found at {dataset_csv}. Set FASHION_DATASET_CSV env var.")
    PRODUCTS = _build_product_catalog()
    print(f"[INFO] Product catalog ready with {len(PRODUCTS)} products.")
    _ensure_demo_accounts()
    print("[INFO] Demo accounts ready: admin@fashionhub.com / user@fashionhub.com")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/signup")
def signup(payload: UserSignup):
    try:
        user = create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            profile={"preferred_styles": payload.preferred_styles, "preferred_colors": payload.preferred_colors, "budget": payload.budget},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    role = user.get("role", "admin" if user["email"].lower() == "admin@fashionhub.com" else "user")
    token = create_access_token(user["id"], user["email"], role)
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "profile": user["profile"], "role": role}}


@app.post("/login")
def login(payload: UserLogin):
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    role = user.get("role", "admin" if user["email"].lower() == "admin@fashionhub.com" else "user")
    token = create_access_token(user["id"], user["email"], role)
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "profile": user["profile"], "role": role}}


@app.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    user = get_user_by_email(payload.email)
    if user:
        token = create_password_reset(payload.email)
        return {"ok": True, "message": "Password reset link generated", "reset_token": token}
    return {"ok": True, "message": "If account exists, reset link has been sent"}


@app.post("/recommend")
def recommend(payload: RecommendRequest):
    if model.df is None or model.item_embeddings is None:
        raise HTTPException(status_code=503, detail="Model not ready. Check dataset configuration.")
    user = get_user_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = user.get("profile", {})
    top_k = max(5, payload.top_k)
    recommendations = model.recommend(
        preferred_styles=profile.get("preferred_styles", []),
        preferred_colors=profile.get("preferred_colors", []),
        history_ids=user.get("history", []),
        top_k=top_k,
        query=payload.query,
        filter_category=payload.filter_category,
        filter_color=payload.filter_color,
    )
    products_by_id = {str(p["id"]): p for p in PRODUCTS}
    rich = build_engine_response(
        recommendations,
        products_by_id,
        profile,
        occasion_hint=payload.occasion,
        season_hint=payload.season,
        gender_hint=payload.gender,
    )
    return rich


@app.post("/save-item")
def save_item(payload: SaveItemRequest):
    user = get_user_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    save_item_for_user(payload.user_id, payload.item_id)

    def updater(existing):
        history = existing.get("history", [])
        if payload.item_id not in history:
            history.append(payload.item_id)
        existing["history"] = history
        return existing

    update_user(payload.user_id, updater)
    return {"ok": True, "saved": get_saved_for_user(payload.user_id)}


@app.get("/saved/{user_id}")
def list_saved(user_id: str):
    return {"saved": get_saved_for_user(user_id)}


@app.delete("/saved/{user_id}/{item_id}")
def unsave_item(user_id: str, item_id: str):
    remove_saved_item_for_user(user_id, item_id)
    return {"ok": True, "saved": get_saved_for_user(user_id)}


@app.get("/categories")
def categories():
    counts: Dict[str, int] = {}
    for product in PRODUCTS:
        counts[product["category"]] = counts.get(product["category"], 0) + 1
    return {"items": [{"name": key, "count": value} for key, value in sorted(counts.items(), key=lambda x: x[0])]}


@app.get("/brands")
def list_brands():
    names = {str(p.get("brand", "")).strip() for p in PRODUCTS if p.get("brand")}
    return {"items": sorted(n for n in names if n)}


@app.get("/products")
def list_products(
    query: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: float = Query(default=0),
    max_price: float = Query(default=999999),
    min_rating: float = Query(default=0, ge=0, le=5),
    sort: str = Query(default="popularity"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=16, ge=1, le=100),
):
    rows = PRODUCTS[:]
    if query:
        q = str(query).strip().lower()
        if q:

            def _haystack(x: Dict[str, Any]) -> str:
                tags = x.get("tags") or []
                tag_str = " ".join(str(t) for t in tags) if isinstance(tags, list) else str(tags)
                parts = [
                    x.get("name", ""),
                    x.get("description", ""),
                    x.get("category", ""),
                    x.get("brand", ""),
                    x.get("color", ""),
                    x.get("style", ""),
                    tag_str,
                    str(x.get("id", "")),
                ]
                return " ".join(str(p) for p in parts).lower()

            def _matches(hay: str) -> bool:
                for token in q.split():
                    t = token.strip()
                    if not t:
                        continue
                    if t not in hay:
                        return False
                return True

            rows = [x for x in rows if _matches(_haystack(x))]
    if category:
        rows = [x for x in rows if x["category"].lower() == category.lower()]
    if brand:
        rows = [x for x in rows if x["brand"].lower() == brand.lower()]
    rows = [x for x in rows if min_price <= float(x["price"]) <= max_price and float(x["rating"]) >= min_rating]
    if sort == "low_to_high":
        rows.sort(key=lambda x: float(x["price"]))
    elif sort == "high_to_low":
        rows.sort(key=lambda x: float(x["price"]), reverse=True)
    elif sort == "newest":
        rows.sort(key=lambda x: str(x["id"]), reverse=True)
    else:
        rows.sort(key=lambda x: (float(x["rating"]), int(x["reviews_count"])), reverse=True)
    total = len(rows)
    start = (page - 1) * limit
    end = start + limit
    return {"items": rows[start:end], "total": total, "page": page, "limit": limit}


@app.get("/products/{product_id}")
def product_detail(product_id: str):
    product = _find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    reviews = get_reviews_for_product(product_id)
    avg_rating = round(sum(x["rating"] for x in reviews) / len(reviews), 2) if reviews else product["rating"]
    return {"product": {**product, "gallery": [product["image"], product["image"], product["image"]], "rating": avg_rating}, "reviews": reviews[-10:][::-1]}


@app.get("/products/{product_id}/reviews")
def product_reviews(product_id: str):
    return {"items": get_reviews_for_product(product_id)}


@app.post("/products/{product_id}/reviews")
def create_review(product_id: str, payload: ReviewCreateRequest):
    if payload.product_id != product_id:
        raise HTTPException(status_code=400, detail="Product mismatch")
    if not _find_product(product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    user = get_user_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    review = add_review(product_id, payload.user_id, payload.rating, payload.comment)
    return {"ok": True, "review": review}


def _hydrate_cart(user_id: str) -> Dict[str, Any]:
    cart_items = get_cart(user_id)
    hydrated: list[Dict[str, Any]] = []
    subtotal = 0.0
    for item in cart_items:
        product = _find_product(item["product_id"])
        if not product:
            continue
        quantity = int(item["quantity"])
        line_total = round(quantity * float(product["price"]), 2)
        subtotal += line_total
        hydrated.append({"product": product, "quantity": quantity, "line_total": line_total})
    shipping = 0 if subtotal >= 999 else 49
    total = round(subtotal + shipping, 2)
    return {"items": hydrated, "subtotal": round(subtotal, 2), "shipping": shipping, "total": total}


@app.get("/cart/{user_id}")
def get_cart_for_user(user_id: str):
    return _hydrate_cart(user_id)


@app.post("/cart/add")
def cart_add(payload: CartItemRequest):
    if not _find_product(payload.product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    existing = get_cart(payload.user_id)
    current = next((x for x in existing if x["product_id"] == payload.product_id), None)
    new_qty = payload.quantity + (current["quantity"] if current else 0)
    add_or_update_cart_item(payload.user_id, payload.product_id, min(new_qty, 20))
    return _hydrate_cart(payload.user_id)


@app.post("/cart/update")
def cart_update(payload: CartUpdateRequest):
    add_or_update_cart_item(payload.user_id, payload.product_id, payload.quantity)
    return _hydrate_cart(payload.user_id)


@app.post("/cart/remove")
def cart_remove(payload: CartRemoveRequest):
    remove_cart_item(payload.user_id, payload.product_id)
    return _hydrate_cart(payload.user_id)


@app.post("/checkout")
def checkout(payload: CheckoutRequest):
    user = get_user_by_id(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cart = _hydrate_cart(payload.user_id)
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")
    payment_method = payload.payment_method.upper()
    if payment_method in {"STRIPE", "RAZORPAY"} and not payload.payment_reference:
        raise HTTPException(status_code=400, detail=f"{payment_method} payment reference required")
    if payment_method in {"STRIPE", "RAZORPAY"} and payload.payment_reference not in VERIFIED_PAYMENTS:
        raise HTTPException(status_code=400, detail=f"{payment_method} payment not verified")
    address = {
        "full_name": payload.full_name,
        "phone": payload.phone,
        "address_line1": payload.address_line1,
        "address_line2": payload.address_line2,
        "city": payload.city,
        "state": payload.state,
        "postal_code": payload.postal_code,
    }
    order = create_order(
        user_id=payload.user_id,
        items=cart["items"],
        subtotal=cart["subtotal"],
        shipping=cart["shipping"],
        total=cart["total"],
        address=address,
        payment_method=payment_method,
    )
    clear_cart(payload.user_id)
    return {"ok": True, "order": order}


@app.get("/orders/{user_id}")
def list_orders(user_id: str):
    return {"items": get_orders_for_user(user_id)[::-1]}


@app.put("/users/{user_id}")
def update_profile(user_id: str, payload: UpdateProfileRequest):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    def updater(existing):
        profile = existing.get("profile", {})
        if payload.name is not None:
            profile["name"] = payload.name
        if payload.phone is not None:
            profile["phone"] = payload.phone
        if payload.preferred_styles is not None:
            profile["preferred_styles"] = payload.preferred_styles
        if payload.preferred_colors is not None:
            profile["preferred_colors"] = payload.preferred_colors
        if payload.budget is not None:
            profile["budget"] = payload.budget
        existing["profile"] = profile
        return existing

    updated = update_user(user_id, updater)
    return {"user": {"id": updated["id"], "email": updated["email"], "profile": updated["profile"]}}


@app.post("/payments/stripe/create-intent")
def create_stripe_intent(payload: StripePaymentIntentRequest):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe key not configured")
    try:
        intent = stripe.PaymentIntent.create(
            amount=payload.amount,
            currency=payload.currency.lower(),
            automatic_payment_methods={"enabled": True},
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Stripe error: {exc}") from exc
    return {"client_secret": intent.client_secret, "payment_intent_id": intent.id}


@app.post("/payments/stripe/confirm/{payment_intent_id}")
def confirm_stripe_payment(payment_intent_id: str):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe key not configured")
    intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    if intent.status not in {"succeeded", "requires_capture"}:
        raise HTTPException(status_code=400, detail=f"Payment not completed ({intent.status})")
    VERIFIED_PAYMENTS.add(payment_intent_id)
    return {"ok": True, "payment_reference": payment_intent_id}


@app.post("/payments/razorpay/create-order")
def create_razorpay_order(payload: RazorpayOrderRequest):
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        raise HTTPException(status_code=500, detail="Razorpay keys not configured")
    try:
        order = razorpay_client.order.create(
            {
                "amount": payload.amount,
                "currency": payload.currency,
                "payment_capture": 1,
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Razorpay error: {exc}") from exc
    return {"order_id": order["id"], "amount": order["amount"], "currency": order["currency"], "key_id": key_id}


@app.post("/payments/razorpay/verify")
def verify_razorpay_payment(payload: Dict[str, str]):
    if payload.get("razorpay_signature") != "demo-signature":
        try:
            razorpay_client.utility.verify_payment_signature(payload)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Razorpay verification failed: {exc}") from exc
    payment_id = payload.get("razorpay_payment_id", "")
    if not payment_id:
        raise HTTPException(status_code=400, detail="Missing razorpay payment id")
    VERIFIED_PAYMENTS.add(payment_id)
    return {"ok": True, "payment_reference": payment_id}


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n"


@app.get("/sitemap.xml", response_class=PlainTextResponse)
def sitemap_xml():
    urls = ["/", "/products", "/auth"]
    urls.extend([f"/products/{x['id']}" for x in PRODUCTS[:500]])
    body = "".join([f"<url><loc>{u}</loc></url>" for u in urls])
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'


@app.get("/ssr/products/{product_id}", response_class=HTMLResponse)
def product_ssr(product_id: str):
    product = _find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    title = f"{product['name']} | FashionHub"
    description = product["description"]
    image = product["image"]
    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <meta name="description" content="{description}" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:image" content="{image}" />
    <meta property="og:type" content="product" />
  </head>
  <body>
    <h1>{product['name']}</h1>
    <p>{description}</p>
    <a href="/products/{product_id}">Open product page</a>
  </body>
</html>"""


@app.get("/admin/orders")
def admin_orders(_: Dict[str, Any] = Depends(require_admin)):
    return {"items": get_all_orders()[::-1]}


@app.get("/admin/users")
def admin_users(_: Dict[str, Any] = Depends(require_admin)):
    users = get_all_users()
    return {"items": [{"id": u["id"], "email": u["email"], "profile": u.get("profile", {})} for u in users]}


@app.get("/admin/products")
def admin_products(_: Dict[str, Any] = Depends(require_admin)):
    return {"items": PRODUCTS}


@app.post("/admin/products")
def admin_create_product(payload: AdminProductUpsertRequest, _: Dict[str, Any] = Depends(require_admin)):
    product = payload.model_dump()
    product["id"] = f"admin_{uuid.uuid4().hex[:8]}"
    product["original_price"] = round(product["price"] * 1.15, 2)
    product["discount_percent"] = 15
    product["reviews_count"] = 0
    product["tags"] = [product["category"], product["brand"]]
    PRODUCTS.append(product)
    return {"ok": True, "product": product}


@app.put("/admin/products/{product_id}")
def admin_update_product(product_id: str, payload: AdminProductUpsertRequest, _: Dict[str, Any] = Depends(require_admin)):
    product = _find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump().items():
        product[key] = value
    product["original_price"] = round(product["price"] * 1.15, 2)
    return {"ok": True, "product": product}


@app.delete("/admin/products/{product_id}")
def admin_delete_product(product_id: str, _: Dict[str, Any] = Depends(require_admin)):
    idx = next((i for i, x in enumerate(PRODUCTS) if str(x["id"]) == str(product_id)), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Product not found")
    PRODUCTS.pop(idx)
    return {"ok": True}

