import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Review, User, Order

app = FastAPI(title="MC Alger Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class Obj(BaseModel):
    id: str


def to_public(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.get("_id"))
    doc.pop("_id", None)
    return doc


@app.get("/")
def read_root():
    return {"message": "MC Alger Store API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()
            response["database"] = "✅ Connected & Working"
    except Exception as e:
        response["database"] = f"⚠️ Error: {str(e)[:80]}"
    return response


# Seed minimal catalog if empty
@app.post("/seed")
def seed_catalog():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    if db["product"].count_documents({}) > 0:
        return {"status": "exists"}

    sample_products = [
        Product(
            title="MC Alger Home Kit 2024",
            description="Official home kit in green with red trim. Lightweight fabric, breathable panels, embroidered crest.",
            price=12999,
            category="t-shirt",
            color="green",
            collection="home",
            sizes=["S","M","L","XL"],
            images=[{"url": "https://images.unsplash.com/photo-1546519638-68e109498ffc?q=80&w=1200", "alt": "Home kit"}],
            rating=4.9,
            reviews_count=128,
            in_stock=True
        ),
        Product(
            title="MCA Training Tracksuit",
            description="High-performance tracksuit with MCA crest. Tapered fit, zip pockets, moisture-wicking.",
            price=18999,
            category="tracksuit",
            color="green",
            collection="training",
            sizes=["M","L","XL"],
            images=[{"url": "https://images.unsplash.com/photo-1511735111819-9a3f7709049c?q=80&w=1200", "alt": "Tracksuit"}],
            rating=4.7,
            reviews_count=76,
            in_stock=True
        ),
        Product(
            title="Retro 1990s Hoodie",
            description="Throwback hoodie inspired by MCA 90s era. Cozy fleece, vintage crest patch.",
            price=14999,
            category="hoodie",
            color="red",
            collection="retro",
            sizes=["S","M","L"],
            images=[{"url": "https://images.unsplash.com/photo-1544025162-d76694265947?q=80&w=1200", "alt": "Retro hoodie"}],
            rating=4.6,
            reviews_count=52,
            in_stock=True
        ),
    ]

    for p in sample_products:
        create_document("product", p)

    return {"status": "seeded", "count": len(sample_products)}


# Products
@app.get("/products")
def list_products(q: Optional[str] = None, category: Optional[str] = None, color: Optional[str] = None, size: Optional[str] = None, collection: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_dict = {}
    if q:
        filter_dict["title"] = {"$regex": q, "$options": "i"}
    if category:
        filter_dict["category"] = category
    if color:
        filter_dict["color"] = color
    if collection:
        filter_dict["collection"] = collection
    if size:
        filter_dict["sizes"] = size

    items = get_documents("product", filter_dict)
    return [to_public(i) for i in items]


@app.get("/products/{product_id}")
def get_product(product_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    doc = db["product"].find_one({"_id": ObjectId(product_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return to_public(doc)


class ReviewIn(Review):
    pass


@app.post("/products/{product_id}/reviews")
def add_review(product_id: str, payload: ReviewIn):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Ensure product exists
    prod = db["product"].find_one({"_id": ObjectId(product_id)})
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    data = payload.model_dump()
    data["product_id"] = product_id
    create_document("review", data)
    return {"status": "ok"}


# Wishlist (anonymous simple endpoint; could be tied to user later)
class WishlistItem(BaseModel):
    product_id: str


@app.post("/wishlist")
def wishlist_add(item: WishlistItem):
    create_document("wishlist", item.model_dump())
    return {"status": "ok"}


# Orders / Checkout (simplified without payments integration for now)
class CheckoutIn(BaseModel):
    items: List[dict]
    email: Optional[str] = None
    shipping_address: Optional[dict] = None


@app.post("/checkout")
def checkout(payload: CheckoutIn):
    total = 0.0
    for it in payload.items:
        total += float(it.get("price", 0)) * int(it.get("qty", 1))
    order = Order(items=[
        {"product_id": i.get("product_id"), "title": i.get("title"), "price": float(i.get("price", 0)), "size": i.get("size"), "qty": int(i.get("qty", 1))}
        for i in payload.items
    ], total=total, currency="DZD", email=payload.email, shipping_address=payload.shipping_address)
    oid = create_document("order", order)
    return {"status": "ok", "order_id": oid, "total": total}


# Schema insight for dev tools
@app.get("/schema")
def schema_overview():
    return {
        "user": User.model_json_schema(),
        "product": Product.model_json_schema(),
        "review": Review.model_json_schema(),
        "order": Order.model_json_schema(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
