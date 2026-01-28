"""
Digital Sahayak - Main Server (Refactored)
FastAPI backend for job and government scheme platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import configuration
from config.settings import (
    APP_NAME, APP_VERSION, DEBUG, ALLOWED_ORIGINS
)
from config.database import Database

# Import routes
from routes import (
    auth_routes,
    job_routes,
    yojana_routes,
    application_routes,
    payment_routes,
    ai_routes,
    scraper_routes_v2,
    whatsapp_routes,
    form_routes,
    apply_ai_v1_routes
)

# Import AI systems
from ai_learning_system import SelfLearningAI
from services.hybrid_matching import HybridMatchingEngine
from services.form_intelligence import FormIntelligenceEngine
from services.scheduler import get_scheduler

# Global instances
db_instance = Database()
self_learning_ai = None
hybrid_matcher = None
form_engine = None
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    global self_learning_ai, hybrid_matcher, form_engine, scheduler
    
    # Startup
    print("🚀 Starting Digital Sahayak Server...")
    
    # Connect to database
    await db_instance.connect()
    print("✅ Connected to MongoDB")
    
    # Initialize AI Learning System
    try:
        self_learning_ai = SelfLearningAI()
        print("✅ Self-Learning AI System initialized")
    except Exception as e:
        print(f"⚠️ AI System initialization failed: {e}")
    
    # Initialize Hybrid Matching Engine
    try:
        hybrid_matcher = HybridMatchingEngine()
        print("✅ Hybrid Matching Engine initialized")
    except Exception as e:
        print(f"⚠️ Hybrid Matcher initialization failed: {e}")
    
    # Initialize Form Intelligence Engine
    try:
        form_engine = FormIntelligenceEngine()
        print("✅ Form Intelligence Engine initialized")
    except Exception as e:
        print(f"⚠️ Form Engine initialization failed: {e}")
    
    # Initialize and start Scraper Scheduler
    try:
        scheduler = get_scheduler()
        await scheduler.start()
        print("✅ Scraper Scheduler started (auto-scraping enabled)")
    except Exception as e:
        print(f"⚠️ Scheduler initialization failed: {e}")
    
    # Set AI instances in routes
    ai_routes.set_ai_instances(self_learning_ai, hybrid_matcher)
    form_routes.set_form_engine(form_engine)
    apply_ai_v1_routes.set_engines(hybrid_matcher, form_engine)
    
    print("✅ Server ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down server...")
    
    # Stop scheduler
    if scheduler:
        await scheduler.stop()
        print("✅ Scheduler stopped")
    
    await db_instance.disconnect()
    print("✅ Database disconnected")

# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Backend API for Digital Sahayak - Job and Government Scheme Platform",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "message": "Digital Sahayak API is running"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected" if db_instance.db else "disconnected",
        "ai_system": "active" if self_learning_ai else "inactive",
        "hybrid_matcher": "active" if hybrid_matcher else "inactive",
        "form_intelligence": "active" if form_engine else "inactive"
    }

# Mount routers
app.include_router(auth_routes.router, prefix="/api")
app.include_router(job_routes.router, prefix="/api")
app.include_router(yojana_routes.router, prefix="/api")
app.include_router(application_routes.router, prefix="/api")
app.include_router(payment_routes.router, prefix="/api")
app.include_router(ai_routes.router, prefix="/api")
app.include_router(scraper_routes_v2.router, prefix="/api")
app.include_router(whatsapp_routes.router, prefix="/api")
app.include_router(form_routes.router, prefix="/api")

# Apply AI Engine v1 - Productized API
app.include_router(apply_ai_v1_routes.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server_refactored:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )
