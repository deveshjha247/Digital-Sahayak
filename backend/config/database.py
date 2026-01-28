"""
Database Configuration and Connection
MongoDB connection and collections
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import MONGO_URL, DB_NAME

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        cls.client = AsyncIOMotorClient(MONGO_URL)
        
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
    
    @classmethod
    def get_db(cls):
        """Get database instance"""
        return cls.client[DB_NAME]
    
    @classmethod
    def get_collection(cls, name: str):
        """Get specific collection"""
        return cls.client[DB_NAME][name]

# Convenience function
def get_database():
    return Database.get_db()
