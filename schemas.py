"""
Database Schemas for MC Alger E‑Commerce

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercased class name by convention in this project.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Hashed password or secret")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL")
    is_active: bool = Field(True, description="Whether user is active")
    wishlist: Optional[List[str]] = Field(default_factory=list, description="List of product ids user likes")
    addresses: Optional[List[dict]] = Field(default_factory=list, description="Saved addresses")


class ProductImage(BaseModel):
    url: str
    alt: Optional[str] = None


class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in DZD or selected currency")
    category: str = Field(..., description="e.g., t-shirt, tracksuit, hoodie")
    color: str = Field(..., description="green | red | white")
    collection: str = Field(..., description="home | training | retro")
    sizes: List[str] = Field(default_factory=list, description="Available sizes: XS..XXL")
    images: List[ProductImage] = Field(default_factory=list)
    rating: float = Field(4.8, ge=0, le=5)
    reviews_count: int = Field(0, ge=0)
    in_stock: bool = Field(True)


class Review(BaseModel):
    product_id: str = Field(..., description="Associated product id")
    user_name: str = Field(...)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class OrderItem(BaseModel):
    product_id: str
    title: str
    price: float
    size: Optional[str] = None
    qty: int = Field(1, ge=1)


class Order(BaseModel):
    user_id: Optional[str] = None
    items: List[OrderItem]
    total: float
    currency: str = Field("DZD")
    status: str = Field("pending")
    email: Optional[EmailStr] = None
    shipping_address: Optional[dict] = None
