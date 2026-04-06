# Using Hugging Face Gemma with Claude Code

This document explains how to integrate the Gemma model with Claude Code.

## Quick Start

### 1. Setup Virtual Environment

Run the setup script to create a venv and install dependencies:

```bash
python setup.py
```

Or manually:

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `.env` and add your Hugging Face API key:

```bash
HF_API_KEY=your_token_here
```

Get your token from: https://huggingface.co/settings/tokens

### 3. Use in Claude Code

In Claude Code, run Python with the virtual environment:

```python
# Add the project to Python path
import sys
sys.path.insert(0, r"D:\httpwww.r-5.org\Python projects\gemma")

# Import the integration
from claude_integration import ask_gemma, analyze_image

# Use the model
response = ask_gemma("What is the capital of France?")
print(response)
```

## Functions Reference

### ask_gemma(prompt, temperature=0.7, max_tokens=None)
Send a text query to the model.

```python
response = ask_gemma("Explain neural networks")
```

### analyze_image(image_url, prompt, temperature=0.7, max_tokens=None)
Analyze an image with a text prompt.

```python
response = analyze_image(
    "https://example.com/image.jpg",
    "What do you see in this image?"
)
```

### chat_with_history(messages, temperature=0.7, max_tokens=None)
Send a conversation with history.

```python
messages = [
    {"role": "system", "content": "You are a coding assistant."},
    {"role": "user", "content": "What is recursion?"}
]
response = chat_with_history(messages)
```

## Testing

Test the integration:

```bash
python claude_integration.py
```

Or run an example:

```bash
python examples/vision_example.py
```

## Model Information

- **Model**: google/gemma-4-31B-it:fastest
- **Provider**: Hugging Face Inference API
- **API**: OpenAI-compatible format
- **Features**: Text generation, vision (image analysis)
