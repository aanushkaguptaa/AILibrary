import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from .config import settings
from .models import ChatRequest, ErrorResponse
from .services import GroqService, conversation_manager
from .utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS origins: {settings.cors_origins_list}")
    
    groq = GroqService()
    is_valid = await groq.validate_api_key()
    if not is_valid:
        logger.warning("⚠️  Groq API key validation failed - check your .env file")
    else:
        logger.info("✓ Groq API key validated successfully")
    
    yield
    
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    description="FastAPI backend with Groq LLM integration and streaming support",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "conversations_in_memory": conversation_manager.get_conversation_count()
    }


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat completion from Groq.
    
    This endpoint accepts a chat request and streams the response back using
    Server-Sent Events (SSE) format.
    
    Args:
        request: ChatRequest with model, prompts, and hyperparameters
        
    Returns:
        StreamingResponse with SSE format
    """
    try:
        logger.info(f"Chat request - Model: {request.model.value}, Save: {request.save_conversation}")
        
        groq = GroqService()
    
        conversation_history = None
        conversation_id = request.conversation_id
        
        if request.save_conversation:
            if not conversation_id:
                conversation_id = conversation_manager.create_conversation()
            elif not conversation_manager.conversation_exists(conversation_id):
                logger.warning(f"Conversation {conversation_id} not found, creating new one")
                conversation_id = conversation_manager.create_conversation()
            
            conversation_history = conversation_manager.get_conversation_history(
                conversation_id,
                max_messages=20  
            )
        
        payload = request.to_messages(conversation_history)
        
        async def generate_stream() -> AsyncGenerator[str, None]:
            """Generate SSE stream."""
            full_response = ""
            
            try:
                yield f"data: {{'conversation_id': '{conversation_id or ''}', 'model': '{request.model.value}'}}\n\n"
                
                async for content in groq.stream_chat_completion(payload):
                    full_response += content
                    yield f"data: {{'content': {repr(content)}, 'finished': false}}\n\n"
                
                yield f"data: {{'content': '', 'finished': true}}\n\n"
                
                if request.save_conversation and conversation_id:
                    if request.system_prompt:
                        conversation_manager.add_message(
                            conversation_id,
                            "system",
                            request.system_prompt
                        )
                    conversation_manager.add_message(
                        conversation_id,
                        "user",
                        request.user_prompt
                    )
                    conversation_manager.add_message(
                        conversation_id,
                        "assistant",
                        full_response
                    )
                    logger.info(f"Saved conversation to {conversation_id}")
                
            except Exception as e:
                logger.error(f"Error during streaming: {e}")
                error_msg = str(e).replace("'", "\\'")
                yield f"data: {{'error': '{error_msg}', 'finished': true}}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in chat_stream: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Internal server error",
                detail=str(e),
                model=request.model.value
            ).model_dump()
        )


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history by ID.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Conversation history
    """
    if not conversation_manager.conversation_exists(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    history = conversation_manager.get_conversation_history(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "messages": [msg.model_dump() for msg in history]
    }


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Success message
    """
    if not conversation_manager.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
