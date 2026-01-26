# AI Library Backend

FastAPI backend with Groq LLM integration and streaming support.

## Features

- ✅ **FastAPI** - Modern, fast web framework
- ✅ **Groq Integration** - Access to fast LLM inference via Groq API
- ✅ **Streaming Responses** - Server-Sent Events (SSE) for real-time streaming
- ✅ **Conversation History** - In-memory storage with MongoDB Atlas ready structure
- ✅ **Model-Specific Validation** - Hyperparameter validation per model
- ✅ **CORS Support** - Configured for local development
- ✅ **Comprehensive Logging** - Request/response logging for debugging

## Supported Models

1. `llama-3.1-8b-instant` - Llama 3.1 8B (fast inference)
2. `openai/gpt-oss-120b` - GPT OSS 120B
3. `qwen/qwen3-32b` - Qwen3 32B
4. `groq/compound` - Groq Compound model

## Hyperparameters

### Supported by All Models
- `temperature` (0.0 - 2.0)
- `top_p` (0.0 - 1.0)
- `max_tokens` (1 - 32000)
- `stop` (array of strings, max 4)

### Model-Specific
- `top_k` (0+) - May not be supported by all models
- `repetition_penalty` (0.0 - 2.0) - May not be supported by all models
- `frequency_penalty` (-2.0 - 2.0)
- `presence_penalty` (-2.0 - 2.0)

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` file and add your Groq API key:

```env
GROQ_API_KEY=your_actual_api_key_here
```

Get your API key from [console.groq.com](https://console.groq.com).

### 3. Run the Server

```bash
# Development mode (with auto-reload)
python -m src.main

# Or using uvicorn directly
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

## API Endpoints

### 1. Chat Stream (POST `/api/chat/stream`)

Stream chat completion with SSE format.

**Request Body:**
```json
{
  "model": "llama-3.1-8b-instant",
  "user_prompt": "Explain quantum computing",
  "system_prompt": "You are a helpful AI assistant.",
  "hyperparameters": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 2048,
    "stop": ["END"]
  },
  "save_conversation": true,
  "conversation_id": null
}
```

**Response:** Server-Sent Events stream
```
data: {'conversation_id': 'abc-123', 'model': 'llama-3.1-8b-instant'}

data: {'content': 'Quantum', 'finished': false}

data: {'content': ' computing', 'finished': false}

data: {'content': '', 'finished': true}
```

### 2. Get Conversation (GET `/api/conversations/{conversation_id}`)

Retrieve conversation history.

**Response:**
```json
{
  "conversation_id": "abc-123",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

### 3. Delete Conversation (DELETE `/api/conversations/{conversation_id}`)

Delete a conversation from memory.

### 4. Health Check (GET `/health`)

Check server status.

**Response:**
```json
{
  "status": "healthy",
  "conversations_in_memory": 5
}
```

## Frontend Integration

### JavaScript/TypeScript Example

```javascript
const response = await fetch('http://localhost:8000/api/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    model: 'llama-3.1-8b-instant',
    user_prompt: 'Write a hello world in Python',
    system_prompt: 'You are a coding assistant.',
    hyperparameters: {
      temperature: 0.7,
      max_tokens: 1024
    },
    save_conversation: false
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      
      if (data.content) {
        console.log(data.content); // Stream content
      }
      
      if (data.finished) {
        console.log('Stream finished');
      }
    }
  }
}
```

## Project Structure

```
ai_library/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   └── chat.py          # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── groq_service.py  # Groq API service
│   │   └── conversation.py  # Conversation manager
│   └── utils/
│       ├── __init__.py
│       └── logging.py       # Logging configuration
├── .env                     # Environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

## Migration to MongoDB Atlas

The conversation manager is designed for easy migration to MongoDB Atlas:

1. Uncomment MongoDB URI in `.env`
2. Update `ConversationManager` in `src/services/conversation.py` to use Motor (async MongoDB driver)
3. Replace in-memory dict with MongoDB collections

## Development Notes

- **Logging**: Set `DEBUG=True` in `.env` for detailed logs
- **CORS**: Update `CORS_ORIGINS` in `.env` for your frontend URL
- **Rate Limiting**: Consider adding rate limiting for production
- **Authentication**: Add API key authentication before deployment

## Troubleshooting

### API Key Issues
- Ensure `GROQ_API_KEY` is set in `.env`
- Get your API key from [console.groq.com](https://console.groq.com)
- Check logs on startup for validation status

### CORS Errors
- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Ensure format is comma-separated: `http://localhost:3000,http://localhost:5173`

### Streaming Not Working
- Check browser console for SSE errors
- Verify `Content-Type: text/event-stream` in response headers
- Some proxies/load balancers may buffer SSE - disable buffering

## License

MIT
