"""
Application Configuration
Centralized settings and environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'digital_sahayak')

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'digital-sahayak-super-secret-key-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Cashfree Configuration
CASHFREE_APP_ID = os.environ.get('CASHFREE_APP_ID', '')
CASHFREE_SECRET_KEY = os.environ.get('CASHFREE_SECRET_KEY', '')
CASHFREE_ENV = os.environ.get('CASHFREE_ENV', 'PRODUCTION')

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'digital_sahayak_verify_token')

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Application Settings
APP_TITLE = "Digital Sahayak API"
APP_VERSION = "2.0.0"
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://digitalsahayak.com",
]

# Logging Configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Admin Credentials
DEFAULT_ADMIN_PHONE = "6200184827"
DEFAULT_ADMIN_PASSWORD = "admin123"
