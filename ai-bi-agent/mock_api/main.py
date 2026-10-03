"""
Mock e-commerce REST API.

⚠️  ALL DATA IS SYNTHETIC — NOT FROM ANY REAL PLATFORM.
This service simulates an external e-commerce system for development and demo purposes.
"""
from fastapi import FastAPI, Query
from mock_api.data import MOCK_CUSTOMERS, MOCK_ORDERS, MOCK_PRODUCTS

app = FastAPI(
    title="Mock E-Commerce API",
    description="⚠️ SYNTHETIC DATA ONLY — simulates an external e-commerce platform.",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok", "note": "This is a mock API with synthetic data."}


@app.get("/customers")
def get_customers(since: str | None = Query(default=None)):
    """Return mock customer records. `since` parameter accepted but not filtered for simplicity."""
    return MOCK_CUSTOMERS


@app.get("/products")
def get_products(since: str | None = Query(default=None)):
    return MOCK_PRODUCTS


@app.get("/orders")
def get_orders(since: str | None = Query(default=None)):
    return MOCK_ORDERS


@app.get("/orders/{order_id}")
def get_order(order_id: str):
    match = next((o for o in MOCK_ORDERS if str(o["order_id"]) == order_id), None)
    if match is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")
    return match
