# Hugging Face Gemma Client

A Python client for interacting with Google's Gemma 4 31B model through Hugging Face's inference API, using the OpenAI-compatible interface.

## Features

- OpenAI SDK-compatible API
- Chat completions with conversation history
- Vision capabilities for image analysis
- Streaming support
- Environment-based configuration

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Configure your API key:**

Copy the example environment file and add your Hugging Face API key:

```bash
cp .env.example .env
```

Then edit `.env` and add your Hugging Face API token from https://huggingface.co/settings/tokens

## Usage

### Basic Chat

```python
from src.hf_client import HuggingFaceGemmaClient

client = HuggingFaceGemmaClient()
response = client.simple_chat("What is machine learning?")
print(response)
```

### Vision (Image Analysis)

```python
from src.hf_client import HuggingFaceGemmaClient

client = HuggingFaceGemmaClient()
response = client.chat_with_image(
    text_prompt="Describe this image in one sentence.",
    image_url="https://example.com/image.jpg"
)
print(response.choices[0].message.content)
```

### Multi-turn Conversation

```python
from src.hf_client import HuggingFaceGemmaClient

client = HuggingFaceGemmaClient()

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
]

response = client.chat(messages, temperature=0.7)
print(response.choices[0].message.content)
```

## Examples

Run the included examples:

```bash
# Basic chat example
python examples/basic_chat.py

# Vision/image analysis example
python examples/vision_example.py

# Interactive chat session
python examples/interactive_chat.py
```

## Configuration

### Hugging Face (Gemma)

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_API_KEY` | Required | Your Hugging Face API token |
| `MODEL_NAME` | `google/gemma-4-31B-it:fastest` | Model identifier |
| `BASE_URL` | `https://router.huggingface.co/v1` | API base URL |

### Z.AI (GLM Models)

| Variable | Default | Description |
|----------|---------|-------------|
| `ZAI_API_KEY` | Required | Your Z.AI API token |
| `ZAI_MODEL` | `glm-4.7` | Default model identifier |
| `ZAI_BASE_URL` | `https://api.z.ai/api/paas/v4` | API base URL |

#### Available Z.AI Models (Free Tier):

**Free Text Models:**
- `glm-4.7-flash` - Fast, free text model
- `glm-4.5-flash` - Lightweight, free text model

**Free Vision Models:**
- `glm-4.6v-flash` - Free vision model

#### Adding Custom Models

You can add any Z.AI model by clicking the **+** button next to the model selector. Enter the model ID (e.g., `glm-5`, `glm-4.7`, etc.) and it will be added to your available models list.

See [Z.AI Pricing](https://docs.z.ai/guides/overview/pricing) for a list of all available models and their pricing.

## Model

This project uses `google/gemma-4-31B-it:fastest` which is optimized for inference speed on Hugging Face's infrastructure.

## Claude Code Integration

This project includes integration with Claude Code for easy access to the Gemma model.

### Using with Claude Code

1. **Quick setup in Claude Code:**

```python
# Import the integration module
import sys
sys.path.insert(0, r"D:\httpwww.r-5.org\Python projects\gemma")
from claude_integration import ask_gemma, analyze_image

# Use the model
response = ask_gemma("Explain machine learning in simple terms")
print(response)

# Analyze an image
response = analyze_image(
    "https://example.com/image.jpg",
    "What's in this image?"
)
print(response)
```

2. **Available functions:**

| Function | Description |
|----------|-------------|
| `ask_gemma(prompt)` | Send a text query |
| `analyze_image(url, prompt)` | Analyze an image |
| `chat_with_history(messages)` | Send conversation history |

3. **Setting up with Claude Code:**

```bash
# In your project directory
python setup.py              # Creates venv and installs dependencies
# Edit .env with your HF_API_KEY
python -m venv venv          # Or manually create venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Then in Claude Code, you can import and use the model:

```python
exec(open('claude_integration.py').read())
response = ask_gemma("Your question here")
```

## Virtual Environment Setup

Create and activate the virtual environment:

```bash
# Option 1: Use the setup script
python setup.py

# Option 2: Manual setup
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Web Chatbot

A Claude-like chat interface is included in the `web/` directory.

### Features

- **Clean, modern UI** similar to Claude
- **Text chat** with streaming responses
- **Image upload** for vision analysis (drag & drop supported)
- **Conversation history** with sidebar
- **SQLite persistence** for chats
- **Responsive design** (works on mobile and desktop)

### Running the Web Chatbot

1. **Install web dependencies:**

```bash
cd web
pip install -r requirements-web.txt
```

2. **Run the Flask server:**

```bash
cd web
python app.py
```

3. **Open in browser:**

Navigate to `http://localhost:5000`

### Web API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send text message |
| `/api/chat/stream` | POST | Stream response with SSE |
| `/api/vision` | POST | Analyze image |
| `/api/conversations` | GET/POST | List/create conversations |
| `/api/upload` | POST | Upload image |

## Project Structure

```
gemma/
├── src/                      # Core Python client
│   ├── hf_client.py
│   └── __init__.py
├── web/                      # Web chatbot
│   ├── app.py               # Flask backend
│   ├── database.py          # SQLite models
│   ├── requirements-web.txt
│   └── static/
│       ├── index.html       # Main page
│       └── js/
│           ├── app.js       # Main app
│           ├── api.js       # API client
│           ├── chat.js      # Chat UI
│           └── sidebar.js   # Sidebar
├── examples/                 # Usage examples
├── claude_integration.py     # Claude Code integration
├── requirements.txt
└── README.md
```

## MCP Server (External Access)

You can use this chatbot as an MCP (Model Context Protocol) server from external applications like Claude Code.

### Setup

1. **Install MCP SDK:**

```bash
pip install mcp
```

2. **Configure Claude Code:**

Add to your Claude Code MCP settings (Settings > MCP):

```json
{
  "mcpServers": {
    "glm-chatbot": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "D:\\httpwww.r-5.org\\Python projects\\gemma"
    }
  }
}
```

### Available MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `send_message` | Send text message to chatbot | `message`, `provider`, `model`, `temperature`, `max_tokens` |
| `analyze_image` | Analyze image with vision model | `image_path`, `prompt`, `provider`, `model` |
| `list_models` | List all available models | None |
| `add_custom_model` | Add custom Z.AI model | `model_id`, `name`, `model_type`, `description` |

### MCP Usage Examples

**Send a message:**
```python
# Use the MCP tool
send_message(
    message="What is machine learning?",
    provider="zai",
    model="glm-4.7-flash"
)
```

**Analyze an image:**
```python
analyze_image(
    image_path="/path/to/image.jpg",
    prompt="What's in this image?",
    model="glm-4.6v-flash"
)
```

**Add a custom model:**
```python
add_custom_model(
    model_id="glm-5",
    name="GLM-5 Premium",
    model_type="text",
    description="Premium GLM-5 model"
)
```

### Running MCP Server Standalone

```bash
# Run the MCP server directly
python mcp_server.py

# Or use stdio transport for MCP clients
python mcp_server.py --transport stdio
```

## License

MIT License
