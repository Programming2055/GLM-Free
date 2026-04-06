#!/usr/bin/env python3
"""Vision example with Hugging Face Gemma model."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.hf_client import HuggingFaceGemmaClient


def main():
    """Run a vision example."""
    # Initialize client
    client = HuggingFaceGemmaClient()

    print("=" * 50)
    print("Vision Example - Image Analysis")
    print("=" * 50)

    # Example with the Statue of Liberty image
    image_url = "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
    prompt = "Describe this image in one sentence."

    print(f"\nImage URL: {image_url}")
    print(f"Prompt: {prompt}\n")
    print("Response:")

    response = client.chat_with_image(
        text_prompt=prompt,
        image_url=image_url,
        temperature=0.7,
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
