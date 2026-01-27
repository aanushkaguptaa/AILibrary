import logging
import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from ..config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """
    MongoDB connection manager using Motor (async MongoDB driver).
    """
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """
        Connect to MongoDB Atlas.
        """
        try:
            if not settings.mongodb_uri:
                raise ValueError("MONGODB_URI not configured in environment variables")
            
            logger.info("Connecting to MongoDB...")

            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                tlsCAFile=certifi.where()
            )
            self.db = self.client[settings.mongodb_db_name]
            
            await self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self) -> None:
        """
        Close MongoDB connection.
        """
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def health_check(self) -> bool:
        """
        Check if MongoDB connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if not self.client:
                return False
            await self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False
    
    def get_collection(self, collection_name: str):
        """
        Get a MongoDB collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Motor collection object
        """
        if self.db is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self.db[collection_name]


mongodb = MongoDB()
