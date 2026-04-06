#!/usr/bin/env python3
"""Basic chat example with Hugging Face Gemma model."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.hf_client import HuggingFaceGemmaClient


def main():
    """Run a basic chat example."""
    # Initialize client
    client = HuggingFaceGemmaClient()

    # Simple chat
    print("=" * 50)
    print("Simple Chat Example")
    print("=" * 50)

    prompt = "What are the key benefits of using open-source AI models?"
    print(f"\nUser: {prompt}\n")

    response = client.simple_chat(prompt, temperature=0.7)
    print(f"Assistant: {response}\n")

    # Multi-turn conversation
    print("=" * 50)
    print("Multi-turn Conversation Example")
    print("=" * 50)

    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "What is the difference between a list and a tuple in Python?"},
    ]

    print(f"\nUser: {messages[1]['content']}\n")
    response = client.chat(messages, temperature=0.7)
    print(f"Assistant: {response.choices[0].message.content}\n")


if __name__ == "__main__":
    main()
