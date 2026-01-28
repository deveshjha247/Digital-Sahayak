"""
WhatsApp Routes
WhatsApp Business API integration (Mock for now)
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from middleware.auth import get_current_admin
from config.database import get_database
from utils.helpers import get_current_timestamp, sanitize_phone
import httpx

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

# WhatsApp Business API credentials (Mock)
WHATSAPP_API_URL = "https://graph.facebook.com/v17.0"
WHATSAPP_TOKEN = "your_whatsapp_token"  # Replace with actual token
WHATSAPP_PHONE_ID = "your_phone_number_id"  # Replace with actual ID

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp messages
    """
    db = get_database()
    
    data = await request.json()
    
    # Parse WhatsApp webhook payload
    entry = data.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})
    
    messages = value.get("messages", [])
    
    for message in messages:
        sender = message.get("from")
        message_type = message.get("type")
        message_id = message.get("id")
        
        # Extract message content
        if message_type == "text":
            text = message.get("text", {}).get("body", "")
        else:
            text = f"[{message_type} message]"
        
        # Save message to database
        message_doc = {
            "message_id": message_id,
            "sender": sender,
            "message_type": message_type,
            "text": text,
            "timestamp": message.get("timestamp"),
            "received_at": get_current_timestamp()
        }
        
        await db.whatsapp_messages.insert_one(message_doc)
        
        # Auto-respond (basic implementation)
        response_text = await generate_whatsapp_response(text, sender, db)
        
        if response_text:
            await send_whatsapp_message(sender, response_text)
    
    return {"status": "ok"}

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """
    Verify WhatsApp webhook
    """
    VERIFY_TOKEN = "your_verify_token"  # Replace with your token
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    
    raise HTTPException(403, "Invalid verification token")

@router.post("/send")
async def send_message(
    phone: str,
    message: str,
    current_user: dict = Depends(get_current_admin)
):
    """
    Send WhatsApp message (Admin only)
    """
    phone = sanitize_phone(phone)
    
    result = await send_whatsapp_message(phone, message)
    
    return result

async def send_whatsapp_message(phone: str, text: str):
    """
    Send WhatsApp message via Business API
    """
    # Mock implementation - replace with actual API call
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text}
    }
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages",
                json=payload,
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {"status": "sent", "data": response.json()}
            else:
                return {"status": "failed", "error": response.text}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def generate_whatsapp_response(message: str, sender: str, db):
    """
    Generate intelligent response based on message
    """
    message_lower = message.lower()
    
    # Basic keyword matching
    if any(word in message_lower for word in ["job", "jobs", "naukri"]):
        # Get latest jobs
        jobs = await db.jobs.find().limit(3).to_list(length=3)
        if jobs:
            response = "📢 Latest Jobs:\n\n"
            for job in jobs:
                response += f"• {job['title']} at {job['company']}\n"
            response += "\nVisit our website for more details!"
            return response
    
    elif any(word in message_lower for word in ["yojana", "scheme", "सरकारी योजना"]):
        # Get latest schemes
        yojanas = await db.yojana.find().limit(3).to_list(length=3)
        if yojanas:
            response = "🏛️ Government Schemes:\n\n"
            for yojana in yojanas:
                response += f"• {yojana['title']}\n"
            response += "\nVisit our website for details!"
            return response
    
    elif any(word in message_lower for word in ["help", "मदद", "सहायता"]):
        return ("👋 Welcome to Digital Sahayak!\n\n"
                "I can help you with:\n"
                "• Job opportunities\n"
                "• Government schemes\n"
                "• Application status\n\n"
                "Just ask me anything!")
    
    else:
        return ("Thank you for your message! Our team will get back to you soon.\n\n"
                "For immediate assistance, visit our website.")
