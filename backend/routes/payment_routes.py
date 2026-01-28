"""
Payment Routes
Cashfree payment integration
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from models.schemas import PaymentCreate, PaymentWebhook
from middleware.auth import get_current_user, get_current_admin
from config.database import get_database
from config.settings import CASHFREE_APP_ID, CASHFREE_SECRET_KEY
from utils.helpers import get_current_timestamp
import uuid
import httpx
import hmac
import hashlib

router = APIRouter(prefix="/payments", tags=["Payments"])

CASHFREE_BASE_URL = "https://api.cashfree.com/pg"

@router.post("/create-order")
async def create_payment_order(
    payment: PaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create Cashfree payment order"""
    db = get_database()
    
    # Create order ID
    order_id = f"ORD_{uuid.uuid4().hex[:12].upper()}"
    
    # Prepare Cashfree order
    cashfree_order = {
        "order_id": order_id,
        "order_amount": payment.amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": current_user["id"],
            "customer_name": current_user["name"],
            "customer_email": current_user.get("email", "user@example.com"),
            "customer_phone": current_user["phone"]
        },
        "order_meta": {
            "return_url": f"{payment.return_url}?order_id={order_id}",
            "notify_url": f"{payment.notify_url}/api/payments/webhook"
        }
    }
    
    # Call Cashfree API
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2022-09-01",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CASHFREE_BASE_URL}/orders",
            json=cashfree_order,
            headers=headers
        )
    
    if response.status_code != 200:
        raise HTTPException(500, "Failed to create payment order")
    
    cashfree_response = response.json()
    
    # Save payment record
    payment_doc = {
        "id": str(uuid.uuid4()),
        "order_id": order_id,
        "user_id": current_user["id"],
        "resource_type": payment.resource_type,
        "resource_id": payment.resource_id,
        "amount": payment.amount,
        "status": "pending",
        "payment_session_id": cashfree_response.get("payment_session_id"),
        "cashfree_order_id": cashfree_response.get("cf_order_id"),
        "created_at": get_current_timestamp()
    }
    
    await db.payments.insert_one(payment_doc)
    
    return {
        "order_id": order_id,
        "payment_session_id": cashfree_response.get("payment_session_id"),
        "payment_url": cashfree_response.get("payment_link")
    }

@router.get("/status/{order_id}")
async def get_payment_status(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get payment status"""
    db = get_database()
    
    payment = await db.payments.find_one({"order_id": order_id})
    
    if not payment:
        raise HTTPException(404, "Payment not found")
    
    # Check ownership or admin
    if payment["user_id"] != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(403, "Not authorized")
    
    # Fetch latest status from Cashfree
    headers = {
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "x-api-version": "2022-09-01"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CASHFREE_BASE_URL}/orders/{order_id}",
            headers=headers
        )
    
    if response.status_code == 200:
        order_data = response.json()
        status = order_data.get("order_status", "PENDING").lower()
        
        # Update local record
        await db.payments.update_one(
            {"order_id": order_id},
            {"$set": {"status": status, "updated_at": get_current_timestamp()}}
        )
        
        payment["status"] = status
    
    return payment

@router.post("/webhook")
async def payment_webhook(request: Request):
    """Cashfree webhook handler"""
    db = get_database()
    
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify signature
    signature = request.headers.get("x-webhook-signature")
    timestamp = request.headers.get("x-webhook-timestamp")
    
    if signature and timestamp:
        expected_signature = hmac.new(
            CASHFREE_SECRET_KEY.encode(),
            f"{timestamp}{body.decode()}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_signature:
            raise HTTPException(401, "Invalid webhook signature")
    
    # Parse webhook data
    data = await request.json()
    
    order_id = data.get("data", {}).get("order", {}).get("order_id")
    status = data.get("data", {}).get("order", {}).get("order_status", "").lower()
    
    if order_id:
        # Update payment status
        await db.payments.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": status,
                    "webhook_data": data,
                    "updated_at": get_current_timestamp()
                }
            }
        )
    
    return {"status": "ok"}

@router.get("/history")
async def get_payment_history(
    current_user: dict = Depends(get_current_user)
):
    """Get user payment history"""
    db = get_database()
    
    payments = await db.payments.find(
        {"user_id": current_user["id"]}
    ).sort("created_at", -1).to_list(length=50)
    
    return {
        "payments": payments,
        "count": len(payments)
    }

@router.get("/all")
async def get_all_payments(
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_admin)
):
    """Get all payments (Admin only)"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    
    payments = await db.payments.find(query).skip(skip).limit(limit).sort("created_at", -1).to_list(length=limit)
    total = await db.payments.count_documents(query)
    
    return {
        "payments": payments,
        "total": total,
        "page": skip // limit + 1
    }
