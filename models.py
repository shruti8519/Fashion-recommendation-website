from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)
    profile = Column(JSON, default=dict)
    history = Column(JSON, default=list)


class SavedItem(Base):
    __tablename__ = "saved_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    item_id = Column(String, nullable=False)


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)


class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    items = Column(JSON, nullable=False)
    subtotal = Column(Float, nullable=False)
    shipping = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    address = Column(JSON, nullable=False)
    payment_method = Column(String, nullable=False)
    status = Column(String, default="Placed")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Review(Base):
    __tablename__ = "reviews"
    id = Column(String, primary_key=True)
    product_id = Column(String, index=True, nullable=False)
    user_id = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PasswordReset(Base):
    __tablename__ = "password_resets"
    token = Column(String, primary_key=True)
    email = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
