"""
Authentication Routes
Login, registration, and user management
"""

from fastapi import APIRouter, HTTPException, Depends
from models.schemas import UserCreate, UserResponse, UserUpdate
from middleware.auth import (
    get_password_hash, verify_password, create_access_token,
    get_current_user
)
from config.database import get_database
from utils.helpers import sanitize_phone, get_current_timestamp
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register(user: UserCreate):
    """Register new user"""
    db = get_database()
    
    # Sanitize phone
    phone = sanitize_phone(user.phone)
    
    # Check if user exists
    existing = await db.users.find_one({"phone": phone})
    if existing:
        raise HTTPException(400, "Phone number already registered")
    
    # Create user document
    user_doc = {
        "id": str(uuid.uuid4()),
        "name": user.name,
        "phone": phone,
        "email": user.email,
        "password": get_password_hash(user.password),
        "language": user.language,
        "is_admin": False,
        "is_operator": False,
        "created_at": get_current_timestamp()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create token
    token = create_access_token({"sub": user_doc["id"]})
    
    return {
        "token": token,
        "user": UserResponse(**{k: v for k, v in user_doc.items() if k != 'password'})
    }

@router.post("/login")
async def login(phone: str, password: str):
    """Login user"""
    db = get_database()
    
    phone = sanitize_phone(phone)
    user = await db.users.find_one({"phone": phone})
    
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(401, "Invalid credentials")
    
    token = create_access_token({"sub": user["id"]})
    
    return {
        "token": token,
        "user": UserResponse(**{k: v for k, v in user.items() if k != 'password'})
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**{k: v for k, v in current_user.items() if k != 'password'})

@router.put("/me")
async def update_me(updates: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update current user profile"""
    db = get_database()
    
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items() if v is not None}
    
    if update_data:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": update_data}
        )
    
    updated_user = await db.users.find_one({"id": current_user["id"]})
    return UserResponse(**{k: v for k, v in updated_user.items() if k != 'password'})
