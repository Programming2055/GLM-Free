"""Flask backend for Gemma Chatbot."""

import sys
import os
import json
import time
from flask import Flask, request, jsonify, Response, stream_with_context, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.hf_client import HuggingFaceGemmaClient
from src.zai_client import ZAIClient, ZAI_MODELS, CUSTOM_MODELS, add_custom_model, get_all_models
from database import Conversation, Message

app = Flask(__name__,
    template_folder='templates',
    static_folder='static'
)
CORS(app)

# Configuration for file uploads
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
ALLOWED_EXTENSIONS = {
    # Images
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg',
    # Documents
    'txt', 'pdf', 'doc', 'docx', 'md', 'csv', 'json', 'xml',
    # Code files
    'py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'h', 'go', 'rs', 'ts', 'tsx', 'jsx',
    # Data files
    'yaml', 'yml', 'toml', 'ini', 'cfg', 'log'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize model clients
clients = {}

def get_client(provider='huggingface'):
    """Get or create a model client for the specified provider."""
    # Handle Z.AI models with specific model IDs (e.g., "zai:glm-4.7-flash")
    if provider.startswith('zai:'):
        model_name = provider[4:]  # Remove "zai:" prefix
        cache_key = provider
        if cache_key not in clients:
            clients[cache_key] = ZAIClient(model_name=model_name)
        return clients[cache_key]

    # Standard providers
    if provider not in clients:
        if provider == 'huggingface':
            clients[provider] = HuggingFaceGemmaClient()
        elif provider == 'zai':
            clients[provider] = ZAIClient()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    return clients[provider]


# ==================== API Routes ====================

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations."""
    conversations = Conversation.get_all()
    return jsonify({"conversations": conversations})


@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation."""
    data = request.get_json() or {}
    title = data.get('title', 'New Chat')

    conversation_id = Conversation.create(title)
    conversation = Conversation.get(conversation_id)

    return jsonify({"conversation": conversation}), 201


@app.route('/api/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation with messages."""
    conversation = Conversation.get(conversation_id)

    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    messages = Message.get_by_conversation(conversation_id)

    return jsonify({
        "conversation": conversation,
        "messages": messages
    })


@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation."""
    Conversation.delete(conversation_id)
    return jsonify({"message": "Conversation deleted"}), 200


@app.route('/api/conversations/<conversation_id>/title', methods=['PUT'])
def update_conversation_title(conversation_id):
    """Update conversation title."""
    data = request.get_json() or {}
    title = data.get('title')

    if not title:
        return jsonify({"error": "Title is required"}), 400

    Conversation.update_title(conversation_id, title)
    return jsonify({"message": "Title updated"}), 200


@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get available model providers."""
    providers = []

    # Check Hugging Face
    try:
        HuggingFaceGemmaClient()
        providers.append({
            "id": "huggingface",
            "name": "Gemma 4 31B",
            "description": "Google's Gemma model via Hugging Face",
            "type": "text",
            "available": True
        })
    except:
        providers.append({
            "id": "huggingface",
            "name": "Gemma 4 31B",
            "description": "Google's Gemma model via Hugging Face",
            "type": "text",
            "available": False
        })

    # Check Z.AI and add all available models
    zai_available = False
    try:
        ZAIClient()
        zai_available = True
    except:
        pass

    # Add all Z.AI models (text and vision - free + custom)
    all_zai_models = get_all_models()

    # Text models group
    for model_id, model_info in all_zai_models.items():
        if model_info['type'] == 'text':
            is_custom = model_info.get('custom', False)
            providers.append({
                "id": f"zai:{model_id}",
                "name": model_info['name'],
                "description": model_info['description'],
                "type": "text",
                "available": zai_available,
                "custom": is_custom,
                "free": model_info.get('free', False)
            })

    # Vision models group (only add if they're available)
    for model_id, model_info in all_zai_models.items():
        if model_info['type'] == 'vision':
            is_custom = model_info.get('custom', False)
            providers.append({
                "id": f"zai:{model_id}",
                "name": model_info['name'],
                "description": model_info['description'],
                "type": "vision",
                "available": zai_available,
                "custom": is_custom,
                "free": model_info.get('free', False)
            })

    return jsonify({"providers": providers})


@app.route('/api/providers/custom', methods=['POST'])
def add_custom_provider():
    """Add a custom Z.AI model."""
    data = request.get_json() or {}

    model_id = data.get('model_id')
    name = data.get('name')
    model_type = data.get('type', 'text')
    description = data.get('description', '')

    if not model_id or not name:
        return jsonify({"error": "model_id and name are required"}), 400

    # Validate model_id format
    if not model_id.replace('-', '').replace('_', '').replace('.', '').isalnum():
        return jsonify({"error": "Invalid model_id format"}), 400

    # Add custom model
    add_custom_model(model_id, name, model_type, description)

    return jsonify({
        "message": f"Custom model '{name}' added successfully",
        "model": {
            "id": f"zai:{model_id}",
            "name": name,
            "type": model_type,
            "description": description
        }
    }), 201


@app.route('/api/chat', methods=['POST'])
def chat():
    """Send a chat message."""
    data = request.get_json() or {}

    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens')
    provider = data.get('provider', 'huggingface')
    thinking = data.get('thinking')

    if not conversation_id:
        return jsonify({"error": "conversation_id is required"}), 400

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    # Get the appropriate client
    try:
        client = get_client(provider)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Get conversation history
    history = Message.get_by_conversation(conversation_id)

    # Build messages array
    messages = []
    for msg in history:
        messages.append({
            "role": msg['role'],
            "content": msg['content']
        })

    # Add user message
    messages.append({"role": "user", "content": user_message})

    # Save user message
    Message.create(conversation_id, 'user', user_message)

    # Update title if this is the first message
    if len(history) == 0:
        title = user_message[:50] + "..." if len(user_message) > 50 else user_message
        Conversation.update_title(conversation_id, title)

    try:
        # Prepare chat parameters
        chat_params = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # Add thinking parameter if specified (for GLM-5 models)
        if thinking is not None:
            chat_params["thinking"] = thinking

        # Get response from the selected model
        response = client.chat(**chat_params)

        assistant_message = response.choices[0].message.content

        # Save assistant message
        Message.create(conversation_id, 'assistant', assistant_message)

        return jsonify({
            "message": {
                "role": "assistant",
                "content": assistant_message
            }
        })

    except Exception as e:
        import traceback
        print(f"Chat error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Send a chat message with streaming response."""
    data = request.get_json() or {}

    conversation_id = data.get('conversation_id')
    user_message = data.get('message')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens')
    provider = data.get('provider', 'huggingface')
    thinking = data.get('thinking')

    if not conversation_id:
        return jsonify({"error": "conversation_id is required"}), 400

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    # Get the appropriate client
    try:
        client = get_client(provider)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Get conversation history
    history = Message.get_by_conversation(conversation_id)

    # Build messages array
    messages = []
    for msg in history:
        messages.append({
            "role": msg['role'],
            "content": msg['content']
        })

    # Add user message
    messages.append({"role": "user", "content": user_message})

    # Save user message
    Message.create(conversation_id, 'user', user_message)

    # Update title if this is the first message
    if len(history) == 0:
        title = user_message[:50] + "..." if len(user_message) > 50 else user_message
        Conversation.update_title(conversation_id, title)

    def generate():
        """Generate SSE stream with actual token streaming."""
        full_response = ""
        buffer = ""
        last_yield_time = time.time()

        try:
            # Prepare chat parameters
            chat_params = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }

            # Add thinking parameter if specified (for GLM-5 models)
            if thinking is not None:
                chat_params["thinking"] = thinking

            # Use actual streaming from the selected API
            response = client.chat(**chat_params)

            for chunk in response:
                # Check if chunk has content
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        content = delta.content
                        full_response += content
                        buffer += content

                        # Yield every 50ms or when buffer has 10+ chars for smoother streaming
                        current_time = time.time()
                        if current_time - last_yield_time > 0.05 or len(buffer) >= 10:
                            yield f"data: {json.dumps({'content': buffer})}\n\n"
                            buffer = ""
                            last_yield_time = current_time

            # Yield any remaining buffer
            if buffer:
                yield f"data: {json.dumps({'content': buffer})}\n\n"

            # Save full response
            if full_response:
                Message.create(conversation_id, 'assistant', full_response)
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            import traceback
            print(f"Streaming error: {str(e)}")
            print(traceback.format_exc())
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/api/vision', methods=['POST'])
def vision():
    """Analyze an image with text prompt."""
    data = request.get_json() or {}

    conversation_id = data.get('conversation_id')
    image_url = data.get('image_url')
    text_prompt = data.get('prompt', 'Describe this image.')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens')
    provider = data.get('provider', 'huggingface')

    if not conversation_id:
        return jsonify({"error": "conversation_id is required"}), 400

    if not image_url:
        return jsonify({"error": "image_url is required"}), 400

    # Get the appropriate client
    try:
        client = get_client(provider)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Save user message with image
    full_content = f"[Image] {text_prompt}"
    Message.create(conversation_id, 'user', full_content, image_url)

    # Update title if first message
    history = Message.get_by_conversation(conversation_id)
    if len(history) <= 1:
        Conversation.update_title(conversation_id, "Image Analysis")

    try:
        # Get response from the selected model
        response = client.chat_with_image(
            text_prompt=text_prompt,
            image_url=image_url,
            temperature=temperature,
            max_tokens=max_tokens
        )

        assistant_message = response.choices[0].message.content

        # Save assistant message
        Message.create(conversation_id, 'assistant', assistant_message)

        return jsonify({
            "message": {
                "role": "assistant",
                "content": assistant_message
            }
        })

    except Exception as e:
        import traceback
        print(f"Vision error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a file and return file info or data URL for images."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Check file size (Flask handles this via MAX_CONTENT_LENGTH, but we check early)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    if file_size > 50 * 1024 * 1024:
        return jsonify({"error": "File too large. Maximum size is 50MB."}), 413

    filename = file.filename
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if not allowed_file(filename):
        return jsonify({"error": f"File type .{ext} not allowed. Allowed types: images, documents, code files."}), 400

    # Handle image files - return data URL for vision API
    image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg'}
    if ext in image_extensions:
        image_data = file.read()
        encoded = base64.b64encode(image_data).decode('utf-8')
        mime_type = file.content_type or f'image/{ext}'
        data_url = f"data:{mime_type};base64,{encoded}"

        return jsonify({
            "type": "image",
            "filename": filename,
            "url": data_url,
            "size": file_size
        })

    # Handle text/code files - read and return content
    text_extensions = {'txt', 'md', 'csv', 'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'log',
                       'py', 'js', 'html', 'css', 'java', 'cpp', 'c', 'h', 'go', 'rs', 'ts', 'tsx', 'jsx'}
    if ext in text_extensions:
        try:
            content = file.read().decode('utf-8', errors='replace')
            return jsonify({
                "type": "text",
                "filename": filename,
                "content": content,
                "size": file_size
            })
        except Exception as e:
            return jsonify({"error": f"Could not read file: {str(e)}"}), 500

    # Handle PDF files - return info only
    if ext == 'pdf':
        pdf_data = file.read()
        encoded = base64.b64encode(pdf_data).decode('utf-8')
        return jsonify({
            "type": "pdf",
            "filename": filename,
            "url": f"data:application/pdf;base64,{encoded}",
            "size": file_size,
            "note": "PDF content should be described or extracted before sending to the model"
        })

    # Handle Word documents
    if ext in {'doc', 'docx'}:
        return jsonify({
            "type": "document",
            "filename": filename,
            "size": file_size,
            "note": "Document content should be extracted before sending to the model"
        })

    return jsonify({"error": "Unsupported file type"}), 400


# ==================== Static Files ====================

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


# ==================== Main ====================

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Multi-Model Chat Server")
    print("=" * 60)
    print("\nAvailable providers:")

    # Hugging Face
    try:
        hf_client = HuggingFaceGemmaClient()
        print(f"  ✓ Hugging Face: {hf_client.model_name}")
    except Exception as e:
        print(f"  ✗ Hugging Face: Not configured")

    # Z.AI
    try:
        zai = ZAIClient()
        print(f"  ✓ Z.AI: Default model {zai.model_name}")
        print(f"\n  Supported Z.AI text models:")
        for model_id, info in ZAI_MODELS.items():
            if info['type'] == 'text':
                print(f"    - {info['name']}: {info['description']}")
    except Exception as e:
        print(f"  ✗ Z.AI: Not configured")

    print("\n" + "=" * 60)
    print("Server running at http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
