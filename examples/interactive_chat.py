#!/usr/bin/env python3
"""Interactive chat with Hugging Face Gemma model."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.hf_client import HuggingFaceGemmaClient


def main():
    """Run an interactive chat session."""
    print("=" * 60)
    print("Interactive Chat with Hugging Face Gemma")
    print("Type 'quit', 'exit', or 'q' to end the conversation")
    print("=" * 60)

    # Initialize client
    try:
        client = HuggingFaceGemmaClient()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nMake sure to set your HF_API_KEY in the .env file")
        sys.exit(1)

    # Store conversation history
    messages = []

    while True:
        # Get user input
        print()
        user_input = input("You: ").strip()

        # Check for exit commands
        if user_input.lower() in ["quit", "exit", "q"]:
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        try:
            # Get response from model
            response = client.chat(messages, temperature=0.7)
            assistant_message = response.choices[0].message.content

            # Add assistant response to history
            messages.append({"role": "assistant", "content": assistant_message})

            print(f"\nAssistant: {assistant_message}")

        except Exception as e:
            print(f"\nError: {e}")
            # Remove the last user message if there was an error
            messages.pop()


if __name__ == "__main__":
    main()
