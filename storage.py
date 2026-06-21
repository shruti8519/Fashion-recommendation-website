import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import and_

from .db import USE_DB, db_session
from .models import CartItem, Order, PasswordReset, Review, SavedItem, User

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
USERS_FILE = DATA_DIR / "users.json"
SAVED_FILE = DATA_DIR / "saved_items.json"
CARTS_FILE = DATA_DIR / "carts.json"
ORDERS_FILE = DATA_DIR / "orders.json"
REVIEWS_FILE = DATA_DIR / "reviews.json"
PASSWORD_RESET_FILE = DATA_DIR / "password_resets.json"


def _ensure_file(path: Path, default_obj: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(default_obj, indent=2), encoding="utf-8")


def _read_json(path: Path, default_obj: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_file(path, default_obj)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def create_user(email: str, password_hash: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    if USE_DB:
        with db_session() as db:
            existing = db.query(User).filter(User.email.ilike(email)).first()
            if existing:
                raise ValueError("User already exists")
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                password_hash=password_hash,
                role=("admin" if email.lower() == "admin@fashionhub.com" else "user"),
                profile=profile,
                history=[],
            )
            db.add(user)
            db.flush()
            return _user_to_dict(user)

    payload = _read_json(USERS_FILE, {"users": []})
    if any(user["email"].lower() == email.lower() for user in payload["users"]):
        raise ValueError("User already exists")

    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": password_hash,
        "role": ("admin" if email.lower() == "admin@fashionhub.com" else "user"),
        "profile": profile,
        "history": [],
    }
    payload["users"].append(user)
    _write_json(USERS_FILE, payload)
    return user


def get_user_by_email(email: str) -> Dict[str, Any] | None:
    if USE_DB:
        with db_session() as db:
            user = db.query(User).filter(User.email.ilike(email)).first()
            return _user_to_dict(user) if user else None

    payload = _read_json(USERS_FILE, {"users": []})
    for user in payload["users"]:
        if user["email"].lower() == email.lower():
            return user
    return None


def get_user_by_id(user_id: str) -> Dict[str, Any] | None:
    if USE_DB:
        with db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            return _user_to_dict(user) if user else None

    payload = _read_json(USERS_FILE, {"users": []})
    for user in payload["users"]:
        if user["id"] == user_id:
            return user
    return None


def update_user(user_id: str, updater) -> Dict[str, Any]:
    if USE_DB:
        with db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            updated = updater(_user_to_dict(user))
            user.profile = updated.get("profile", {})
            user.history = updated.get("history", [])
            user.role = updated.get("role", user.role)
            db.flush()
            return _user_to_dict(user)

    payload = _read_json(USERS_FILE, {"users": []})
    for idx, user in enumerate(payload["users"]):
        if user["id"] == user_id:
            updated = updater(user)
            payload["users"][idx] = updated
            _write_json(USERS_FILE, payload)
            return updated
    raise ValueError("User not found")


def save_item_for_user(user_id: str, item_id: str) -> None:
    if USE_DB:
        with db_session() as db:
            exists = db.query(SavedItem).filter(and_(SavedItem.user_id == user_id, SavedItem.item_id == item_id)).first()
            if not exists:
                db.add(SavedItem(user_id=user_id, item_id=item_id))
        return

    payload = _read_json(SAVED_FILE, {"saved": {}})
    payload["saved"].setdefault(user_id, [])
    if item_id not in payload["saved"][user_id]:
        payload["saved"][user_id].append(item_id)
    _write_json(SAVED_FILE, payload)


def get_saved_for_user(user_id: str) -> list[str]:
    if USE_DB:
        with db_session() as db:
            rows = db.query(SavedItem).filter(SavedItem.user_id == user_id).all()
            return [x.item_id for x in rows]

    payload = _read_json(SAVED_FILE, {"saved": {}})
    return payload["saved"].get(user_id, [])


def remove_saved_item_for_user(user_id: str, item_id: str) -> None:
    if USE_DB:
        with db_session() as db:
            db.query(SavedItem).filter(and_(SavedItem.user_id == user_id, SavedItem.item_id == item_id)).delete()
        return

    payload = _read_json(SAVED_FILE, {"saved": {}})
    payload["saved"].setdefault(user_id, [])
    payload["saved"][user_id] = [x for x in payload["saved"][user_id] if x != item_id]
    _write_json(SAVED_FILE, payload)


def create_password_reset(email: str) -> str:
    if USE_DB:
        token = str(uuid.uuid4())
        with db_session() as db:
            db.add(PasswordReset(token=token, email=email))
        return token

    payload = _read_json(PASSWORD_RESET_FILE, {"resets": []})
    token = str(uuid.uuid4())
    payload["resets"].append(
        {
            "token": token,
            "email": email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _write_json(PASSWORD_RESET_FILE, payload)
    return token


def get_cart(user_id: str) -> list[Dict[str, Any]]:
    if USE_DB:
        with db_session() as db:
            rows = db.query(CartItem).filter(CartItem.user_id == user_id).all()
            return [{"product_id": x.product_id, "quantity": x.quantity} for x in rows]

    payload = _read_json(CARTS_FILE, {"carts": {}})
    return payload["carts"].get(user_id, [])


def add_or_update_cart_item(user_id: str, product_id: str, quantity: int) -> list[Dict[str, Any]]:
    if USE_DB:
        with db_session() as db:
            row = db.query(CartItem).filter(and_(CartItem.user_id == user_id, CartItem.product_id == product_id)).first()
            if row:
                row.quantity = quantity
            else:
                db.add(CartItem(user_id=user_id, product_id=product_id, quantity=quantity))
        return get_cart(user_id)

    payload = _read_json(CARTS_FILE, {"carts": {}})
    payload["carts"].setdefault(user_id, [])
    items = payload["carts"][user_id]
    idx = next((i for i, x in enumerate(items) if x["product_id"] == product_id), None)
    if idx is None:
        items.append({"product_id": product_id, "quantity": quantity})
    else:
        items[idx]["quantity"] = quantity
    _write_json(CARTS_FILE, payload)
    return items


def remove_cart_item(user_id: str, product_id: str) -> list[Dict[str, Any]]:
    if USE_DB:
        with db_session() as db:
            db.query(CartItem).filter(and_(CartItem.user_id == user_id, CartItem.product_id == product_id)).delete()
        return get_cart(user_id)

    payload = _read_json(CARTS_FILE, {"carts": {}})
    payload["carts"].setdefault(user_id, [])
    payload["carts"][user_id] = [x for x in payload["carts"][user_id] if x["product_id"] != product_id]
    _write_json(CARTS_FILE, payload)
    return payload["carts"][user_id]


def clear_cart(user_id: str) -> None:
    if USE_DB:
        with db_session() as db:
            db.query(CartItem).filter(CartItem.user_id == user_id).delete()
        return

    payload = _read_json(CARTS_FILE, {"carts": {}})
    payload["carts"][user_id] = []
    _write_json(CARTS_FILE, payload)


def create_order(
    user_id: str,
    items: list[Dict[str, Any]],
    subtotal: float,
    shipping: float,
    total: float,
    address: Dict[str, Any],
    payment_method: str,
) -> Dict[str, Any]:
    if USE_DB:
        order_id = str(uuid.uuid4())
        with db_session() as db:
            db.add(
                Order(
                    id=order_id,
                    user_id=user_id,
                    items=items,
                    subtotal=subtotal,
                    shipping=shipping,
                    total=total,
                    address=address,
                    payment_method=payment_method,
                    status="Placed",
                    created_at=datetime.utcnow(),
                )
            )
        return {
            "id": order_id,
            "user_id": user_id,
            "items": items,
            "subtotal": subtotal,
            "shipping": shipping,
            "total": total,
            "address": address,
            "payment_method": payment_method,
            "status": "Placed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    payload = _read_json(ORDERS_FILE, {"orders": []})
    order = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
        "address": address,
        "payment_method": payment_method,
        "status": "Placed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    payload["orders"].append(order)
    _write_json(ORDERS_FILE, payload)
    return order


def get_orders_for_user(user_id: str) -> list[Dict[str, Any]]:
    if USE_DB:
        with db_session() as db:
            rows = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
            return [_order_to_dict(x) for x in rows]

    payload = _read_json(ORDERS_FILE, {"orders": []})
    return [x for x in payload["orders"] if x["user_id"] == user_id]


def get_all_orders() -> list[Dict[str, Any]]:
    if USE_DB:
        with db_session() as db:
            rows = db.query(Order).order_by(Order.created_at.desc()).all()
            return [_order_to_dict(x) for x in rows]

    payload = _read_json(ORDERS_FILE, {"orders": []})
    return payload["orders"]


def add_review(product_id: str, user_id: str, rating: int, comment: str) -> Dict[str, Any]:
    if USE_DB:
        review_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        with db_session() as db:
            db.add(
                Review(
                    id=review_id,
                    product_id=product_id,
                    user_id=user_id,
                    rating=rating,
                    comment=comment,
                    created_at=created_at,
                )
            )
        return {
            "id": review_id,
            "product_id": product_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "created_at": created_at.isoformat(),
        }

    payload = _read_json(REVIEWS_FILE, {"reviews": []})
    review = {
        "id": str(uuid.uuid4()),
        "product_id": product_id,
        "user_id": user_id,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    payload["reviews"].append(review)
    _write_json(REVIEWS_FILE, payload)
    return review


def get_reviews_for_product(product_id: str) -> list[Dict[str, Any]]:
    if USE_DB:
        with db_session() as db:
            rows = db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()
            return [_review_to_dict(x) for x in rows]

    payload = _read_json(REVIEWS_FILE, {"reviews": []})
    return [x for x in payload["reviews"] if x["product_id"] == product_id]


def get_all_users() -> list[Dict[str, Any]]:
    if USE_DB:
        with db_session() as db:
            return [_user_to_dict(x) for x in db.query(User).all()]

    payload = _read_json(USERS_FILE, {"users": []})
    return payload["users"]


def migrate_json_to_postgres() -> Dict[str, int]:
    if not USE_DB:
        return {"users": 0, "saved": 0, "carts": 0, "orders": 0, "reviews": 0}
    counts = {"users": 0, "saved": 0, "carts": 0, "orders": 0, "reviews": 0}
    users_payload = _read_json(USERS_FILE, {"users": []})
    saved_payload = _read_json(SAVED_FILE, {"saved": {}})
    carts_payload = _read_json(CARTS_FILE, {"carts": {}})
    orders_payload = _read_json(ORDERS_FILE, {"orders": []})
    reviews_payload = _read_json(REVIEWS_FILE, {"reviews": []})

    with db_session() as db:
        if db.query(User).count() > 0:
            return counts
        for user in users_payload.get("users", []):
            db.add(
                User(
                    id=user["id"],
                    email=user["email"],
                    password_hash=user["password_hash"],
                    role=user.get("role", "user"),
                    profile=user.get("profile", {}),
                    history=user.get("history", []),
                )
            )
            counts["users"] += 1
        for user_id, item_ids in saved_payload.get("saved", {}).items():
            for item_id in item_ids:
                db.add(SavedItem(user_id=user_id, item_id=item_id))
                counts["saved"] += 1
        for user_id, items in carts_payload.get("carts", {}).items():
            for item in items:
                db.add(CartItem(user_id=user_id, product_id=item["product_id"], quantity=int(item["quantity"])))
                counts["carts"] += 1
        for order in orders_payload.get("orders", []):
            db.add(
                Order(
                    id=order["id"],
                    user_id=order["user_id"],
                    items=order["items"],
                    subtotal=order["subtotal"],
                    shipping=order["shipping"],
                    total=order["total"],
                    address=order["address"],
                    payment_method=order["payment_method"],
                    status=order.get("status", "Placed"),
                    created_at=datetime.fromisoformat(order["created_at"].replace("Z", "+00:00")),
                )
            )
            counts["orders"] += 1
        for review in reviews_payload.get("reviews", []):
            db.add(
                Review(
                    id=review["id"],
                    product_id=review["product_id"],
                    user_id=review["user_id"],
                    rating=review["rating"],
                    comment=review["comment"],
                    created_at=datetime.fromisoformat(review["created_at"].replace("Z", "+00:00")),
                )
            )
            counts["reviews"] += 1
    return counts


def _user_to_dict(user: User) -> Dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "password_hash": user.password_hash,
        "profile": user.profile or {},
        "history": user.history or [],
        "role": user.role or "user",
    }


def _order_to_dict(order: Order) -> Dict[str, Any]:
    return {
        "id": order.id,
        "user_id": order.user_id,
        "items": order.items,
        "subtotal": order.subtotal,
        "shipping": order.shipping,
        "total": order.total,
        "address": order.address,
        "payment_method": order.payment_method,
        "status": order.status,
        "created_at": order.created_at.isoformat(),
    }


def _review_to_dict(review: Review) -> Dict[str, Any]:
    return {
        "id": review.id,
        "product_id": review.product_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at.isoformat(),
    }

