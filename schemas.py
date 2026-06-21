from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    preferred_styles: List[str] = []
    preferred_colors: List[str] = []
    budget: Optional[float] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RecommendRequest(BaseModel):
    user_id: str
    top_k: int = Field(default=12, ge=1, le=50)
    query: Optional[str] = None
    filter_category: Optional[str] = None
    filter_color: Optional[str] = None
    occasion: Optional[str] = None
    season: Optional[str] = None
    gender: Optional[str] = None


class SaveItemRequest(BaseModel):
    user_id: str
    item_id: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    preferred_styles: Optional[List[str]] = None
    preferred_colors: Optional[List[str]] = None
    budget: Optional[float] = None


class CartItemRequest(BaseModel):
    user_id: str
    product_id: str
    quantity: int = Field(default=1, ge=1, le=20)


class CartUpdateRequest(BaseModel):
    user_id: str
    product_id: str
    quantity: int = Field(ge=1, le=20)


class CartRemoveRequest(BaseModel):
    user_id: str
    product_id: str


class CheckoutRequest(BaseModel):
    user_id: str
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=8, max_length=20)
    address_line1: str = Field(min_length=4, max_length=200)
    address_line2: Optional[str] = Field(default="", max_length=200)
    city: str = Field(min_length=2, max_length=80)
    state: str = Field(min_length=2, max_length=80)
    postal_code: str = Field(min_length=3, max_length=20)
    payment_method: str = Field(default="COD", max_length=40)
    payment_reference: Optional[str] = None


class ReviewCreateRequest(BaseModel):
    user_id: str
    product_id: str
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=3, max_length=500)


class AdminProductUpsertRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=2, max_length=60)
    brand: str = Field(min_length=2, max_length=80)
    price: float = Field(gt=0)
    rating: float = Field(ge=0, le=5)
    description: str = Field(min_length=8, max_length=1000)
    image: str
    stock: int = Field(ge=0, le=10000)


class StripePaymentIntentRequest(BaseModel):
    amount: int = Field(gt=0, description="Amount in paise/cents smallest currency unit")
    currency: str = Field(default="inr", max_length=10)


class RazorpayOrderRequest(BaseModel):
    amount: int = Field(gt=0, description="Amount in paise")
    currency: str = Field(default="INR", max_length=10)

