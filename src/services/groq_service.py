import logging
from typing import AsyncGenerator, Optional, List
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..config import settings

logger = logging.getLogger(__name__)


class GroqService:
    """Service for interacting with Groq API using LangChain."""
    
    def __init__(self):
        self.api_key = settings.groq_api_key
        
    def _create_llm(self, model: str, hyperparameters: dict) -> ChatGroq:
        """
        Create a LangChain ChatGroq instance.
        
        Args:
            model: Model name
            hyperparameters: Generation hyperparameters
            
        Returns:
            Configured ChatGroq instance
        """
        langchain_params = {
            "model": model,
            "groq_api_key": self.api_key,
            "streaming": True,
        }
        
        if "temperature" in hyperparameters:
            langchain_params["temperature"] = hyperparameters["temperature"]
        if "max_tokens" in hyperparameters:
            langchain_params["max_tokens"] = hyperparameters["max_tokens"]
    
        # Add model_kwargs for parameters not directly supported
        model_kwargs = {}
        if "top_p" in hyperparameters:
            model_kwargs["top_p"] = hyperparameters["top_p"]
        if "stop" in hyperparameters and hyperparameters["stop"]:
            langchain_params["stop"] = hyperparameters["stop"]
        
        if model_kwargs:
            langchain_params["model_kwargs"] = model_kwargs
        
        return ChatGroq(**langchain_params)
    
    def _convert_to_langchain_messages(self, messages: list) -> list:
        """
        Convert message dictionaries to LangChain message objects.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            List of LangChain message objects
        """
        langchain_messages = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
        
        return langchain_messages
    
    async def stream_chat_completion(
        self,
        payload: dict
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from Groq API using LangChain.
        
        Args:
            payload: Request payload with model, messages, and parameters
            
        Yields:
            Content chunks from the streaming response
            
        Raises:
            Exception: If the API request fails
        """
        try:
            model = payload.get("model")
            messages = payload.get("messages", [])
            
            # Extract hyperparameters
            hyperparameters = {
                k: v for k, v in payload.items() 
                if k not in ["model", "messages", "stream"]
            }
            
            logger.info(f"Sending request to Groq: model={model}")
            
            # Create LLM instance
            llm = self._create_llm(model, hyperparameters)
            
            # Convert messages to LangChain format
            langchain_messages = self._convert_to_langchain_messages(messages)
            
            # Stream the response
            async for chunk in llm.astream(langchain_messages):
                if chunk.content:
                    yield chunk.content
            
            logger.info("Stream completed")
                    
        except Exception as e:
            logger.error(f"Unexpected error in stream_chat_completion: {e}")
            raise
    
    async def validate_api_key(self) -> bool:
        """
        Validate the Groq API key.
        
        Returns:
            True if the API key is valid, False otherwise
        """
        try:
            # Try to create a simple LLM instance and make a test call
            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                groq_api_key=self.api_key,
                max_tokens=1
            )
            
            # Make a minimal test request
            messages = [HumanMessage(content="Hi")]
            response = await llm.ainvoke(messages)
            
            return True
        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
            return False
