import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime
from ..models.chat import ChatMessage

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation history in-memory.
    
    This is designed to be easily swappable with MongoDB Atlas in the future.
    """
    
    def __init__(self):
        self._conversations: Dict[str, dict] = {}
    
    def create_conversation(self) -> str:
        """
        Create a new conversation.
        
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        self._conversations[conversation_id] = {
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        logger.info(f"Created new conversation: {conversation_id}")
        return conversation_id
    
    def add_message(
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
        if conversation_id not in self._conversations:
            logger.warning(f"Conversation {conversation_id} not found, creating new one")
            self._conversations[conversation_id] = {
                "messages": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._conversations[conversation_id]["messages"].append(message)
        self._conversations[conversation_id]["updated_at"] = datetime.utcnow()
        
        logger.debug(f"Added {role} message to conversation {conversation_id}")
    
    def get_conversation_history(
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
        if conversation_id not in self._conversations:
            logger.warning(f"Conversation {conversation_id} not found")
            return []
        
        messages = self._conversations[conversation_id]["messages"]
        
        if max_messages:
            messages = messages[-max_messages:]
        
        return [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
    
    def conversation_exists(self, conversation_id: str) -> bool:
        """
        Check if a conversation exists.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            True if conversation exists, False otherwise
        """
        return conversation_id in self._conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False
    
    def get_conversation_count(self) -> int:
        """Get total number of conversations in memory."""
        return len(self._conversations)
    
    def clear_all(self) -> None:
        """Clear all conversations (useful for testing)."""
        self._conversations.clear()
        logger.info("Cleared all conversations")


conversation_manager = ConversationManager()
