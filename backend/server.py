from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Query, Body, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import httpx
import json
import hashlib
import hmac
import asyncio
import re
from bs4 import BeautifulSoup
from openai import OpenAI

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'digital-sahayak-super-secret-key-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cashfree Configuration
CASHFREE_APP_ID = os.environ.get('CASHFREE_APP_ID', '')
CASHFREE_SECRET_KEY = os.environ.get('CASHFREE_SECRET_KEY', '')
CASHFREE_ENV = os.environ.get('CASHFREE_ENV', 'PRODUCTION')

# WhatsApp Configuration (MOCK for now)
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'digital_sahayak_verify_token')

# OpenAI Configuration (Emergent LLM Key)
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
openai_client = OpenAI(api_key=EMERGENT_LLM_KEY) if EMERGENT_LLM_KEY else None

app = FastAPI(title="Digital Sahayak API", version="1.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== MODELS =====================

class UserCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: str
    password: str
    language: str = "hi"

class UserLogin(BaseModel):
    phone: str
    password: str

class UserProfile(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: str
    language: str = "hi"
    is_admin: bool = False
    is_operator: bool = False
    documents: List[Dict] = []
    whatsapp_connected: bool = False
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class JobAlertCreate(BaseModel):
    title: str
    title_hi: Optional[str] = None
    organization: str
    organization_hi: Optional[str] = None
    description: str
    description_hi: Optional[str] = None
    vacancies: int = 0
    qualification: str
    qualification_hi: Optional[str] = None
    age_limit: str = ""
    salary: str = ""
    last_date: str
    apply_link: str
    category: str = "government"
    state: str = "all"
    is_active: bool = True

class YojanaCreate(BaseModel):
    name: str
    name_hi: Optional[str] = None
    ministry: str
    ministry_hi: Optional[str] = None
    description: str
    description_hi: Optional[str] = None
    benefits: str
    benefits_hi: Optional[str] = None
    eligibility: str
    eligibility_hi: Optional[str] = None
    documents_required: List[str] = []
    apply_link: str
    category: str = "welfare"
    state: str = "all"
    govt_fee: float = 0
    service_fee: float = 20
    is_active: bool = True

class ApplicationCreate(BaseModel):
    item_type: str  # "job" or "yojana"
    item_id: str
    user_details: Dict[str, Any]
    documents: List[str] = []

class PaymentCreate(BaseModel):
    application_id: str
    amount: float
    return_url: str

class WhatsAppMessage(BaseModel):
    phone: str
    message: str
    template: Optional[str] = None

# ===================== HELPER FUNCTIONS =====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(user: dict = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ===================== AUTH ENDPOINTS =====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"phone": user_data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "phone": user_data.phone,
        "password": get_password_hash(user_data.password),
        "language": user_data.language,
        "is_admin": False,
        "is_operator": False,
        "documents": [],
        "whatsapp_connected": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_access_token({"sub": user_id})
    user_doc.pop("password")
    user_doc.pop("_id", None)
    user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    
    return TokenResponse(access_token=token, user=UserProfile(**user_doc))

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"phone": credentials.phone})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"]})
    user.pop("password")
    user.pop("_id", None)
    if isinstance(user["created_at"], str):
        user["created_at"] = datetime.fromisoformat(user["created_at"])
    
    return TokenResponse(access_token=token, user=UserProfile(**user))

@api_router.get("/auth/me", response_model=UserProfile)
async def get_me(user: dict = Depends(get_current_user)):
    if isinstance(user["created_at"], str):
        user["created_at"] = datetime.fromisoformat(user["created_at"])
    return UserProfile(**user)

# ===================== JOB ALERTS ENDPOINTS =====================

@api_router.post("/jobs", status_code=201)
async def create_job(job: JobAlertCreate, admin: dict = Depends(get_admin_user)):
    job_id = str(uuid.uuid4())
    job_doc = {
        "id": job_id,
        **job.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin["id"],
        "views": 0,
        "applications": 0
    }
    await db.jobs.insert_one(job_doc)
    job_doc.pop("_id", None)
    return job_doc

@api_router.get("/jobs")
async def get_jobs(
    category: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    query = {"is_active": True}
    if category:
        query["category"] = category
    if state and state != "all":
        query["state"] = {"$in": [state, "all"]}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"title_hi": {"$regex": search, "$options": "i"}},
            {"organization": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.jobs.count_documents(query)
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"total": total, "jobs": jobs}

@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.jobs.update_one({"id": job_id}, {"$inc": {"views": 1}})
    return job

@api_router.put("/jobs/{job_id}")
async def update_job(job_id: str, job: JobAlertCreate, admin: dict = Depends(get_admin_user)):
    result = await db.jobs.update_one({"id": job_id}, {"$set": job.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job updated"}

@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.jobs.delete_one({"id": job_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted"}

# ===================== YOJANA ENDPOINTS =====================

@api_router.post("/yojana", status_code=201)
async def create_yojana(yojana: YojanaCreate, admin: dict = Depends(get_admin_user)):
    yojana_id = str(uuid.uuid4())
    yojana_doc = {
        "id": yojana_id,
        **yojana.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin["id"],
        "views": 0,
        "applications": 0
    }
    await db.yojana.insert_one(yojana_doc)
    yojana_doc.pop("_id", None)
    return yojana_doc

@api_router.get("/yojana")
async def get_yojana_list(
    category: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    query = {"is_active": True}
    if category:
        query["category"] = category
    if state and state != "all":
        query["state"] = {"$in": [state, "all"]}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"name_hi": {"$regex": search, "$options": "i"}},
            {"ministry": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.yojana.count_documents(query)
    yojanas = await db.yojana.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"total": total, "yojanas": yojanas}

@api_router.get("/yojana/{yojana_id}")
async def get_yojana(yojana_id: str):
    yojana = await db.yojana.find_one({"id": yojana_id}, {"_id": 0})
    if not yojana:
        raise HTTPException(status_code=404, detail="Yojana not found")
    await db.yojana.update_one({"id": yojana_id}, {"$inc": {"views": 1}})
    return yojana

@api_router.put("/yojana/{yojana_id}")
async def update_yojana(yojana_id: str, yojana: YojanaCreate, admin: dict = Depends(get_admin_user)):
    result = await db.yojana.update_one({"id": yojana_id}, {"$set": yojana.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Yojana not found")
    return {"message": "Yojana updated"}

@api_router.delete("/yojana/{yojana_id}")
async def delete_yojana(yojana_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.yojana.delete_one({"id": yojana_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Yojana not found")
    return {"message": "Yojana deleted"}

# ===================== APPLICATION ENDPOINTS =====================

@api_router.post("/applications", status_code=201)
async def create_application(app_data: ApplicationCreate, user: dict = Depends(get_current_user)):
    app_id = str(uuid.uuid4())
    
    # Get item details
    if app_data.item_type == "job":
        item = await db.jobs.find_one({"id": app_data.item_id}, {"_id": 0})
        service_fee = 20
        govt_fee = 0
    else:
        item = await db.yojana.find_one({"id": app_data.item_id}, {"_id": 0})
        service_fee = item.get("service_fee", 20) if item else 20
        govt_fee = item.get("govt_fee", 0) if item else 0
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    total_fee = service_fee + govt_fee
    
    application_doc = {
        "id": app_id,
        "user_id": user["id"],
        "item_type": app_data.item_type,
        "item_id": app_data.item_id,
        "item_title": item.get("title") or item.get("name"),
        "user_details": app_data.user_details,
        "documents": app_data.documents,
        "service_fee": service_fee,
        "govt_fee": govt_fee,
        "total_fee": total_fee,
        "payment_status": "pending",
        "application_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.applications.insert_one(application_doc)
    
    # Update item application count
    collection = db.jobs if app_data.item_type == "job" else db.yojana
    await collection.update_one({"id": app_data.item_id}, {"$inc": {"applications": 1}})
    
    application_doc.pop("_id", None)
    return application_doc

@api_router.get("/applications")
async def get_user_applications(user: dict = Depends(get_current_user)):
    apps = await db.applications.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"applications": apps}

@api_router.get("/applications/{app_id}")
async def get_application(app_id: str, user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id, "user_id": user["id"]}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

# ===================== PAYMENT ENDPOINTS (Cashfree) =====================

@api_router.post("/payments/create-order")
async def create_payment_order(payment: PaymentCreate, user: dict = Depends(get_current_user)):
    application = await db.applications.find_one({"id": payment.application_id, "user_id": user["id"]})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    
    # Cashfree API call
    cashfree_url = "https://api.cashfree.com/pg/orders" if CASHFREE_ENV == "PRODUCTION" else "https://sandbox.cashfree.com/pg/orders"
    
    headers = {
        "x-api-version": "2023-08-01",
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "order_id": order_id,
        "order_amount": payment.amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": user["id"][:20],
            "customer_name": user["name"],
            "customer_phone": user["phone"],
            "customer_email": user.get("email") or f"{user['phone']}@digitalsahayak.com"
        },
        "order_meta": {
            "return_url": payment.return_url + f"?order_id={order_id}",
            "notify_url": f"{os.environ.get('BACKEND_URL', '')}/api/payments/webhook"
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(cashfree_url, json=payload, headers=headers)
            cf_response = response.json()
            
            if response.status_code in [200, 201]:
                # Store payment record
                payment_doc = {
                    "id": str(uuid.uuid4()),
                    "order_id": order_id,
                    "cf_order_id": cf_response.get("cf_order_id"),
                    "application_id": payment.application_id,
                    "user_id": user["id"],
                    "amount": payment.amount,
                    "status": "PENDING",
                    "payment_session_id": cf_response.get("payment_session_id"),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.payments.insert_one(payment_doc)
                
                return {
                    "order_id": order_id,
                    "payment_session_id": cf_response.get("payment_session_id"),
                    "order_status": cf_response.get("order_status")
                }
            else:
                logger.error(f"Cashfree error: {cf_response}")
                raise HTTPException(status_code=400, detail=cf_response.get("message", "Payment creation failed"))
    except httpx.HTTPError as e:
        logger.error(f"Payment API error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")

@api_router.get("/payments/verify/{order_id}")
async def verify_payment(order_id: str, user: dict = Depends(get_current_user)):
    payment = await db.payments.find_one({"order_id": order_id, "user_id": user["id"]}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Verify with Cashfree
    cashfree_url = f"https://api.cashfree.com/pg/orders/{order_id}" if CASHFREE_ENV == "PRODUCTION" else f"https://sandbox.cashfree.com/pg/orders/{order_id}"
    
    headers = {
        "x-api-version": "2023-08-01",
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(cashfree_url, headers=headers)
            cf_response = response.json()
            
            if response.status_code == 200:
                order_status = cf_response.get("order_status")
                
                # Update payment status
                await db.payments.update_one(
                    {"order_id": order_id},
                    {"$set": {"status": order_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                
                # If paid, update application
                if order_status == "PAID":
                    await db.applications.update_one(
                        {"id": payment["application_id"]},
                        {"$set": {"payment_status": "paid", "application_status": "processing"}}
                    )
                
                return {"order_id": order_id, "status": order_status, "amount": cf_response.get("order_amount")}
            else:
                raise HTTPException(status_code=400, detail="Failed to verify payment")
    except httpx.HTTPError as e:
        logger.error(f"Payment verify error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")

@api_router.post("/payments/webhook")
async def payment_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-webhook-signature")
    
    # Verify webhook signature (simplified)
    logger.info(f"Payment webhook received")
    
    try:
        payload = json.loads(body)
        event_type = payload.get("type")
        data = payload.get("data", {})
        
        if event_type == "PAYMENT_SUCCESS":
            order_id = data.get("order", {}).get("order_id")
            if order_id:
                await db.payments.update_one(
                    {"order_id": order_id},
                    {"$set": {"status": "PAID", "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                payment = await db.payments.find_one({"order_id": order_id})
                if payment:
                    await db.applications.update_one(
                        {"id": payment["application_id"]},
                        {"$set": {"payment_status": "paid", "application_status": "processing"}}
                    )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error"}

# ===================== WHATSAPP ENDPOINTS (MOCK) =====================

@api_router.get("/whatsapp/webhook")
async def whatsapp_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    if hub_verify_token == WHATSAPP_VERIFY_TOKEN and hub_mode == "subscribe":
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@api_router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    body = await request.json()
    logger.info(f"WhatsApp webhook: {json.dumps(body, indent=2)}")
    
    # Process incoming messages (MOCK)
    try:
        if body.get("entry"):
            for entry in body["entry"]:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for msg in messages:
                        sender = msg.get("from")
                        text = msg.get("text", {}).get("body", "")
                        logger.info(f"WhatsApp message from {sender}: {text}")
                        
                        # Store message
                        await db.whatsapp_messages.insert_one({
                            "id": str(uuid.uuid4()),
                            "from": sender,
                            "text": text,
                            "direction": "inbound",
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}")
    
    return {"status": "ok"}

@api_router.post("/whatsapp/send")
async def send_whatsapp(msg: WhatsAppMessage, admin: dict = Depends(get_admin_user)):
    # MOCK implementation - logs the message
    logger.info(f"[MOCK] WhatsApp send to {msg.phone}: {msg.message}")
    
    message_doc = {
        "id": str(uuid.uuid4()),
        "to": msg.phone,
        "text": msg.message,
        "template": msg.template,
        "direction": "outbound",
        "status": "sent",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.whatsapp_messages.insert_one(message_doc)
    message_doc.pop("_id", None)
    
    return {"status": "sent", "message_id": message_doc["id"]}

@api_router.post("/whatsapp/connect")
async def connect_whatsapp(phone: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
    # Update user's WhatsApp connection status
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"whatsapp_connected": True, "whatsapp_phone": phone}}
    )
    return {"status": "connected", "message": "WhatsApp connected successfully"}

# ===================== ADMIN ENDPOINTS =====================

@api_router.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    total_users = await db.users.count_documents({})
    total_jobs = await db.jobs.count_documents({})
    total_yojana = await db.yojana.count_documents({})
    total_applications = await db.applications.count_documents({})
    paid_applications = await db.applications.count_documents({"payment_status": "paid"})
    
    # Revenue calculation
    payments = await db.payments.find({"status": "PAID"}, {"_id": 0, "amount": 1}).to_list(1000)
    total_revenue = sum(p.get("amount", 0) for p in payments)
    
    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_yojana": total_yojana,
        "total_applications": total_applications,
        "paid_applications": paid_applications,
        "total_revenue": total_revenue
    }

@api_router.get("/admin/applications")
async def get_all_applications(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    admin: dict = Depends(get_admin_user)
):
    query = {}
    if status:
        query["application_status"] = status
    
    total = await db.applications.count_documents(query)
    apps = await db.applications.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"total": total, "applications": apps}

@api_router.put("/admin/applications/{app_id}/status")
async def update_application_status(
    app_id: str,
    status: str = Body(..., embed=True),
    admin: dict = Depends(get_admin_user)
):
    result = await db.applications.update_one(
        {"id": app_id},
        {"$set": {"application_status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Status updated"}

@api_router.post("/admin/make-admin")
async def make_admin(phone: str = Body(..., embed=True), admin: dict = Depends(get_admin_user)):
    result = await db.users.update_one({"phone": phone}, {"$set": {"is_admin": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User is now admin"}

# ===================== DOCUMENT ENDPOINTS =====================

@api_router.post("/documents/upload")
async def upload_document(
    doc_type: str = Body(...),
    doc_name: str = Body(...),
    doc_url: str = Body(...),
    user: dict = Depends(get_current_user)
):
    doc = {
        "id": str(uuid.uuid4()),
        "type": doc_type,
        "name": doc_name,
        "url": doc_url,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$push": {"documents": doc}}
    )
    return doc

@api_router.get("/documents")
async def get_documents(user: dict = Depends(get_current_user)):
    return {"documents": user.get("documents", [])}

@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    await db.users.update_one(
        {"id": user["id"]},
        {"$pull": {"documents": {"id": doc_id}}}
    )
    return {"message": "Document deleted"}

# ===================== PUBLIC ENDPOINTS =====================

@api_router.get("/")
async def root():
    return {"message": "Digital Sahayak API v1.0", "status": "online"}

@api_router.get("/categories")
async def get_categories():
    return {
        "job_categories": [
            {"id": "government", "name": "Government Jobs", "name_hi": "सरकारी नौकरी"},
            {"id": "railway", "name": "Railway Jobs", "name_hi": "रेलवे नौकरी"},
            {"id": "bank", "name": "Bank Jobs", "name_hi": "बैंक नौकरी"},
            {"id": "ssc", "name": "SSC Jobs", "name_hi": "SSC नौकरी"},
            {"id": "upsc", "name": "UPSC Jobs", "name_hi": "UPSC नौकरी"},
            {"id": "state", "name": "State Jobs", "name_hi": "राज्य नौकरी"},
            {"id": "defence", "name": "Defence Jobs", "name_hi": "रक्षा नौकरी"},
            {"id": "police", "name": "Police Jobs", "name_hi": "पुलिस नौकरी"}
        ],
        "yojana_categories": [
            {"id": "welfare", "name": "Welfare Schemes", "name_hi": "कल्याण योजना"},
            {"id": "education", "name": "Education", "name_hi": "शिक्षा योजना"},
            {"id": "agriculture", "name": "Agriculture", "name_hi": "कृषि योजना"},
            {"id": "housing", "name": "Housing", "name_hi": "आवास योजना"},
            {"id": "health", "name": "Health", "name_hi": "स्वास्थ्य योजना"},
            {"id": "women", "name": "Women & Child", "name_hi": "महिला एवं बाल"},
            {"id": "pension", "name": "Pension", "name_hi": "पेंशन योजना"},
            {"id": "employment", "name": "Employment", "name_hi": "रोजगार योजना"}
        ],
        "states": [
            {"id": "all", "name": "All India", "name_hi": "संपूर्ण भारत"},
            {"id": "bihar", "name": "Bihar", "name_hi": "बिहार"},
            {"id": "jharkhand", "name": "Jharkhand", "name_hi": "झारखंड"},
            {"id": "up", "name": "Uttar Pradesh", "name_hi": "उत्तर प्रदेश"},
            {"id": "mp", "name": "Madhya Pradesh", "name_hi": "मध्य प्रदेश"},
            {"id": "rajasthan", "name": "Rajasthan", "name_hi": "राजस्थान"},
            {"id": "maharashtra", "name": "Maharashtra", "name_hi": "महाराष्ट्र"},
            {"id": "wb", "name": "West Bengal", "name_hi": "पश्चिम बंगाल"}
        ]
    }

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("phone", unique=True)
    await db.users.create_index("id", unique=True)
    await db.jobs.create_index("id", unique=True)
    await db.jobs.create_index([("created_at", -1)])
    await db.yojana.create_index("id", unique=True)
    await db.yojana.create_index([("created_at", -1)])
    await db.applications.create_index("id", unique=True)
    await db.applications.create_index("user_id")
    await db.payments.create_index("order_id", unique=True)
    
    # Create default admin if not exists
    admin = await db.users.find_one({"phone": "6200184827"})
    if not admin:
        admin_doc = {
            "id": str(uuid.uuid4()),
            "name": "Admin",
            "email": "admin@digitalsahayak.com",
            "phone": "6200184827",
            "password": get_password_hash("admin123"),
            "language": "hi",
            "is_admin": True,
            "is_operator": True,
            "documents": [],
            "whatsapp_connected": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_doc)
        logger.info("Default admin created")
    else:
        # Ensure existing user is admin
        await db.users.update_one({"phone": "6200184827"}, {"$set": {"is_admin": True, "is_operator": True}})
    
    logger.info("Digital Sahayak API started")

@app.on_event("shutdown")
async def shutdown():
    client.close()
