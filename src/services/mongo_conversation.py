import uuid
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from .database import mongodb
from ..models.chat import ChatMessage
from ..config import settings

logger = logging.getLogger(__name__)


class MongoConversationManager:
    """
    Manages conversation history in MongoDB Atlas.
    
    This replaces the in-memory ConversationManager with persistent storage.
    """
    
    def __init__(self):
        self.collection_name = "conversations"
    
    @property
    def collection(self):
        """Get the conversations collection."""
        return mongodb.get_collection(self.collection_name)
    
    async def create_conversation(self, temporary: bool = True) -> str:
        """
        Create a new conversation.
        
        Args:
            temporary: If True, conversation will auto-delete after TTL period
        
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        document = {
            "_id": conversation_id,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "temporary": temporary
        }
        
        if temporary:
            document["expires_at"] = datetime.utcnow() + timedelta(hours=settings.conversation_ttl_hours)
        
        await self.collection.insert_one(document)
        logger.info(f"Created new {'temporary' if temporary else 'permanent'} conversation: {conversation_id}")
        return conversation_id
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            role: Message role (system, user, assistant)
            content: Message content
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        conversation = await self.collection.find_one({"_id": conversation_id})
        
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found, creating new one")
            new_doc = {
                "_id": conversation_id,
                "messages": [message],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "temporary": True,
                "expires_at": datetime.utcnow() + timedelta(hours=settings.conversation_ttl_hours)
            }
            await self.collection.insert_one(new_doc)
        else:
            update_fields = {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.utcnow()}
            }
            
            if conversation.get("temporary", True):
                update_fields["$set"]["expires_at"] = datetime.utcnow() + timedelta(hours=settings.conversation_ttl_hours)
            
            await self.collection.update_one(
                {"_id": conversation_id},
                update_fields
            )
        
        logger.debug(f"Added {role} message to conversation {conversation_id}")
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        max_messages: Optional[int] = None
    ) -> List[ChatMessage]:
        """
        Get conversation history.
        
        Args:
            conversation_id: ID of the conversation
            max_messages: Maximum number of recent messages to return
            
        Returns:
            List of ChatMessage objects
        """
        conversation = await self.collection.find_one({"_id": conversation_id})
        
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return []
        
        messages = conversation.get("messages", [])
        
        if max_messages:
            messages = messages[-max_messages:]
        
        return [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
    
    async def conversation_exists(self, conversation_id: str) -> bool:
        """
        Check if a conversation exists.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            True if conversation exists, False otherwise
        """
        count = await self.collection.count_documents({"_id": conversation_id})
        return count > 0
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({"_id": conversation_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False
    
    async def get_conversation_count(self) -> int:
        """Get total number of conversations in database."""
        return await self.collection.count_documents({})
    
    async def clear_all(self) -> None:
        """Clear all conversations (useful for testing)."""
        await self.collection.delete_many({})
        logger.info("Cleared all conversations")
    
    async def ensure_indexes(self) -> None:
        """
        Create indexes for better query performance and TTL.
        """
        try:
            if mongodb.db is None:
                logger.warning("MongoDB not connected, skipping index creation")
                return
            
            await self.collection.create_index([("created_at", -1)])
            await self.collection.create_index([("updated_at", -1)])
            await self.collection.create_index(
                [("expires_at", 1)],
                expireAfterSeconds=0,
                name="expires_at_ttl"
            )
            logger.info(f"Ensured MongoDB indexes for conversations collection (TTL: {settings.conversation_ttl_hours}h)")
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")


mongo_conversation_manager = MongoConversationManager()
