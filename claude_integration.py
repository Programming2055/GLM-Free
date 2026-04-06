#!/usr/bin/env python3
"""
Claude Code Integration for Hugging Face Gemma Model

This module provides a simple interface for Claude Code to use the Gemma model.

Usage in Claude Code:
    from claude_integration import ask_gemma, analyze_image

    # Simple text query
    response = ask_gemma("Explain quantum computing")

    # Analyze an image
    response = analyze_image("https://example.com/image.jpg", "What's in this image?")
"""

import os
import sys
from typing import Optional

# Ensure src is in path
sys.path.insert(0, os.path.dirname(__file__))

from src.hf_client import HuggingFaceGemmaClient

# Global client instance (initialized lazily)
_client: Optional[HuggingFaceGemmaClient] = None


def _get_client() -> HuggingFaceGemmaClient:
    """Get or create the global client instance."""
    global _client
    if _client is None:
        _client = HuggingFaceGemmaClient()
    return _client


def ask_gemma(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    conversation_history: Optional[list] = None
) -> str:
    """
    Send a text query to the Gemma model.

    Args:
        prompt: The text prompt to send.
        temperature: Sampling temperature (0-2). Higher = more random.
        max_tokens: Maximum tokens to generate.
        conversation_history: Optional list of previous messages for context.

    Returns:
        The model's response as a string.

    Example:
        >>> response = ask_gemma("What is Python?")
        >>> print(response)
    """
    client = _get_client()

    messages = conversation_history or []
    messages.append({"role": "user", "content": prompt})

    response = client.chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content


def analyze_image(
    image_url: str,
    prompt: str = "Describe this image in detail.",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    """
    Analyze an image using the Gemma model's vision capabilities.

    Args:
        image_url: URL of the image to analyze.
        prompt: Text prompt to accompany the image.
        temperature: Sampling temperature (0-2).
        max_tokens: Maximum tokens to generate.

    Returns:
        The model's analysis as a string.

    Example:
        >>> response = analyze_image(
        ...     "https://example.com/photo.jpg",
        ...     "What's happening in this photo?"
        ... )
    """
    client = _get_client()

    response = client.chat_with_image(
        text_prompt=prompt,
        image_url=image_url,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content


def chat_with_history(
    messages: list,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    """
    Send a conversation with multiple messages to the Gemma model.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        temperature: Sampling temperature (0-2).
        max_tokens: Maximum tokens to generate.

    Returns:
        The model's response as a string.

    Example:
        >>> messages = [
        ...     {"role": "system", "content": "You are a helpful assistant."},
        ...     {"role": "user", "content": "What is 2+2?"}
        ... ]
        >>> response = chat_with_history(messages)
    """
    client = _get_client()

    response = client.chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # Test the integration
    print("Testing Gemma integration...")

    # Test text query
    print("\n1. Testing text query:")
    try:
        response = ask_gemma("Hello! What model are you?")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure HF_API_KEY is set in your .env file!")

    # Test image analysis
    print("\n2. Testing image analysis:")
    try:
        response = analyze_image(
            "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg",
            "Describe this landmark."
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
