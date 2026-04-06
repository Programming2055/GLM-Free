"""
Hugging Face Inference Client for Gemma Model
Compatible with OpenAI SDK format
"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class HuggingFaceGemmaClient:
    """Client for interacting with Hugging Face's Gemma model via OpenAI-compatible API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        Initialize the Hugging Face client.

        Args:
            api_key: Hugging Face API key. Defaults to HF_API_KEY env variable.
            base_url: Base URL for the API. Defaults to Hugging Face router.
            model_name: Model identifier. Defaults to google/gemma-4-31B-it:fastest.
        """
        self.api_key = api_key or os.getenv("HF_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set HF_API_KEY environment variable or pass api_key."
            )

        self.base_url = base_url or os.getenv("BASE_URL", "https://router.huggingface.co/v1")
        self.model_name = model_name or os.getenv("MODEL_NAME", "google/gemma-4-31B-it:fastest")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Any:
        """
        Send a chat completion request.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream the response.

        Returns:
            Chat completion response.
        """
        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

    def chat_with_image(
        self,
        text_prompt: str,
        image_url: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """
        Send a vision completion request with an image.

        Args:
            text_prompt: Text prompt to accompany the image.
            image_url: URL of the image to analyze.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.

        Returns:
            Chat completion response.
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text_prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ]

        return self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def simple_chat(self, prompt: str, **kwargs) -> str:
        """
        Simple chat interface that returns just the text response.

        Args:
            prompt: The user's prompt.
            **kwargs: Additional parameters for the chat method.

        Returns:
            The assistant's response text.
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat(messages, **kwargs)
        return response.choices[0].message.content
