"""
Apply AI Engine - API Key Authentication Middleware
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.database import get_database
from datetime import datetime

security = HTTPBearer()

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verify API key for Apply AI Engine v1
    """
    api_key = credentials.credentials
    db = get_database()
    
    # Find API key in database
    key_data = await db.api_keys.find_one({"key": api_key})
    
    if not key_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Check if key is active
    if not key_data.get("is_active", True):
        raise HTTPException(
            status_code=403,
            detail="API key is inactive"
        )
    
    # Check expiration
    expires_at = key_data.get("expires_at")
    if expires_at:
        if datetime.fromisoformat(expires_at) < datetime.now():
            raise HTTPException(
                status_code=403,
                detail="API key has expired"
            )
    
    # Check credits (for paid plans)
    plan = key_data.get("plan", "free")
    if plan != "enterprise":
        credits = key_data.get("credits_remaining", 0)
        if credits <= 0:
            raise HTTPException(
                status_code=402,
                detail="Insufficient credits. Please upgrade your plan."
            )
    
    # Log usage
    await db.api_usage.insert_one({
        "api_key": api_key,
        "organization": key_data.get("organization"),
        "timestamp": datetime.now().isoformat(),
        "endpoint": "unknown"  # Will be set by endpoint
    })
    
    # Decrement credits
    if plan != "enterprise":
        await db.api_keys.update_one(
            {"key": api_key},
            {"$inc": {"credits_remaining": -1}}
        )
    
    return api_key

async def verify_admin_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Verify admin API key for privileged operations
    """
    api_key = credentials.credentials
    db = get_database()
    
    key_data = await db.api_keys.find_one({"key": api_key})
    
    if not key_data:
        raise HTTPException(401, "Invalid API key")
    
    if not key_data.get("is_admin", False):
        raise HTTPException(403, "Admin privileges required")
    
    return api_key
