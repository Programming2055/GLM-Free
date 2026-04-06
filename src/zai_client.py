"""
Z.AI API Client for GLM Models
Compatible with OpenAI SDK format
Supports all Z.AI models including text, vision, audio, image, and video.
"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Available Z.AI Models (Free tier only by default)
ZAI_MODELS = {
    # Text Models (Free tier)
    "glm-4.7-flash": {"name": "GLM-4.7-Flash", "type": "text", "description": "Fast, free text model", "free": True},
    "glm-4.5-flash": {"name": "GLM-4.5-Flash", "type": "text", "description": "Lightweight, free text model", "free": True},

    # Vision Models (Free tier)
    "glm-4.6v-flash": {"name": "GLM-4.6V-Flash", "type": "vision", "description": "Free vision model", "free": True},
}

# Custom models storage (user-added models)
CUSTOM_MODELS = {}


def add_custom_model(model_id: str, name: str, model_type: str = "text", description: str = ""):
    """Add a custom model to the available models list."""
    CUSTOM_MODELS[model_id.lower()] = {
        "name": name,
        "type": model_type,
        "description": description or f"Custom {model_type} model",
        "custom": True
    }


def get_all_models():
    """Get all available models including custom ones."""
    all_models = {**ZAI_MODELS, **CUSTOM_MODELS}
    return all_models


class ZAIClient:
    """Client for interacting with Z.AI's GLM models via OpenAI-compatible API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        Initialize the Z.AI client.

        Args:
            api_key: Z.AI API key. Defaults to ZAI_API_KEY env variable.
            base_url: Base URL for the API. Defaults to Z.AI endpoint.
            model_name: Model identifier. Defaults to glm-4.7.
        """
        self.api_key = api_key or os.getenv("ZAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Z.AI API key is required. Set ZAI_API_KEY environment variable or pass api_key."
            )

        self.base_url = base_url or os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/paas/v4")
        self.model_name = model_name or os.getenv("ZAI_MODEL", "glm-4.7")

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = 4096,
        stream: bool = False,
        thinking: Optional[bool] = None,
    ) -> Any:
        """
        Send a chat completion request.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream the response.
            thinking: Whether to enable thinking mode (only for supported models like GLM-5).

        Returns:
            Chat completion response.
        """
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        # Add thinking parameter only for models that support it (GLM-5 series)
        if thinking is not None and self.model_name.startswith(('glm-5', 'GLM-5')):
            params["thinking"] = {"type": "enabled" if thinking else "disabled"}

        return self.client.chat.completions.create(**params)

    def chat_with_image(
        self,
        text_prompt: str,
        image_url: str,
        temperature: float = 1.0,
        max_tokens: Optional[int] = 4096,
        stream: bool = False,
    ) -> Any:
        """
        Send a vision completion request with an image.

        Args:
            text_prompt: Text prompt to accompany the image.
            image_url: URL of the image to analyze.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream the response.

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
            stream=stream,
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
