#!/usr/bin/env python3
"""MCP Server for GLM-Free Chatbot

This server exposes your chatbot as an MCP (Model Context Protocol) server,
allowing Claude Code and other MCP clients to interact with it.

Installation:
    pip install mcp

Running:
    python mcp_server.py

Or with Claude Code MCP config:
    {
        "mcpServers": {
            "glm-chatbot": {
                "command": "python",
                "args": ["mcp_server.py"],
                "cwd": "D:\\httpwww.r-5.org\\Python projects\\gemma"
            }
        }
    }
"""

import sys
import os
import asyncio

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.types import (
    TextContent,
    Tool,
    ServerCapabilities,
)
from mcp.server.stdio import stdio_server

from src.hf_client import HuggingFaceGemmaClient
from src.zai_client import ZAIClient, add_custom_model, get_all_models


class GLMChatbotMCPServer:
    """MCP Server for GLM-Free Chatbot."""

    def __init__(self):
        self.server = Server("glm-chatbot")
        self._clients = {}

        # Register handlers
        self.server.list_tools_handler(self._list_tools)
        self.server.call_tool_handler(self._call_tool)

    def get_client(self, provider='huggingface', model_name=None):
        """Get or create a model client."""
        cache_key = f"{provider}:{model_name or 'default'}"
        if cache_key not in self._clients:
            if provider == 'huggingface':
                self._clients[cache_key] = HuggingFaceGemmaClient()
            elif provider == 'zai':
                self._clients[cache_key] = ZAIClient(model_name=model_name)
            else:
                raise ValueError(f"Unknown provider: {provider}")
        return self._clients[cache_key]

    async def _list_tools(self) -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="send_message",
                description="Send a text message to the chatbot and get a response. "
                           "Supports both Hugging Face Gemma and Z.AI GLM models.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to send to the chatbot"
                        },
                        "provider": {
                            "type": "string",
                            "description": "Provider to use: 'huggingface' or 'zai'",
                            "enum": ["huggingface", "zai"],
                            "default": "zai"
                        },
                        "model": {
                            "type": "string",
                            "description": "Model name (for Z.AI): glm-4.7-flash, glm-4.5-flash, glm-4.6v-flash",
                            "default": "glm-4.7-flash"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Sampling temperature (0-2)",
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens to generate",
                            "default": 4096
                        }
                    },
                    "required": ["message"]
                }
            ),
            Tool(
                name="analyze_image",
                description="Analyze an image using vision-capable models like GLM-4.6V-Flash",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to local image file or URL"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Question or instruction about the image",
                            "default": "Describe this image in detail."
                        },
                        "provider": {
                            "type": "string",
                            "description": "Provider to use",
                            "enum": ["huggingface", "zai"],
                            "default": "zai"
                        },
                        "model": {
                            "type": "string",
                            "description": "Vision model to use",
                            "default": "glm-4.6v-flash"
                        }
                    },
                    "required": ["image_path"]
                }
            ),
            Tool(
                name="list_models",
                description="List all available models including free and custom models",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="add_custom_model",
                description="Add a custom Z.AI model (e.g., glm-5, glm-4.7) to the available models list",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_id": {
                            "type": "string",
                            "description": "The model ID (e.g., glm-4.7, glm-5-turbo)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Display name for the model"
                        },
                        "model_type": {
                            "type": "string",
                            "description": "Type of model",
                            "enum": ["text", "vision"],
                            "default": "text"
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description of the model"
                        }
                    },
                    "required": ["model_id", "name"]
                }
            ),
        ]

    async def _call_tool(self, name: str, arguments: dict) -> list[TextContent]:
        """Execute a tool call."""
        try:
            if name == "send_message":
                return await self._send_message(arguments)
            elif name == "analyze_image":
                return await self._analyze_image(arguments)
            elif name == "list_models":
                return await self._list_models()
            elif name == "add_custom_model":
                return await self._add_custom_model(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _send_message(self, arguments: dict) -> list[TextContent]:
        """Send a message and return the response."""
        message = arguments["message"]
        provider = arguments.get("provider", "zai")
        model = arguments.get("model", "glm-4.7-flash")
        temperature = arguments.get("temperature", 0.7)
        max_tokens = arguments.get("max_tokens", 4096)

        client = self.get_client(provider, model if provider == "zai" else None)

        messages = [{"role": "user", "content": message}]
        response = client.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )

        content = response.choices[0].message.content
        return [TextContent(type="text", text=content)]

    async def _analyze_image(self, arguments: dict) -> list[TextContent]:
        """Analyze an image and return the response."""
        image_path = arguments["image_path"]
        prompt = arguments.get("prompt", "Describe this image in detail.")
        provider = arguments.get("provider", "zai")
        model = arguments.get("model", "glm-4.6v-flash")

        # Convert local path to data URL if needed
        if os.path.exists(image_path):
            import base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            ext = image_path.split(".")[-1].lower()
            mime_type = f"image/{ext}" if ext in ["png", "jpg", "jpeg", "gif", "webp"] else "image/png"
            image_url = f"data:{mime_type};base64,{image_data}"
        else:
            # Assume it's a URL
            image_url = image_path

        client = self.get_client(provider, model if provider == "zai" else None)

        response = client.chat_with_image(
            text_prompt=prompt,
            image_url=image_url,
            temperature=0.7,
            max_tokens=4096
        )

        content = response.choices[0].message.content
        return [TextContent(type="text", text=content)]

    async def _list_models(self) -> list[TextContent]:
        """List all available models."""
        models_info = ["**Available Models:**\n"]

        # Hugging Face
        try:
            HuggingFaceGemmaClient()
            models_info.append("\n**Hugging Face:**")
            models_info.append("- `huggingface` → Gemma 4 31B")
        except:
            models_info.append("\n**Hugging Face:** Not configured")

        # Z.AI models
        models_info.append("\n**Z.AI Models (Free Tier):**")
        all_models = get_all_models()
        for model_id, info in all_models.items():
            free_tag = " ✅ Free" if info.get("free") else ""
            custom_tag = " ⭐ Custom" if info.get("custom") else ""
            models_info.append(f"- `{model_id}` → {info['name']}: {info['description']}{free_tag}{custom_tag}")

        models_info.append("\n**Usage:**")
        models_info.append("- For Z.AI: Set provider='zai', model='glm-4.7-flash'")
        models_info.append("- For HuggingFace: Set provider='huggingface'")

        return [TextContent(type="text", text="\n".join(models_info))]

    async def _add_custom_model(self, arguments: dict) -> list[TextContent]:
        """Add a custom model."""
        model_id = arguments["model_id"]
        name = arguments["name"]
        model_type = arguments.get("model_type", "text")
        description = arguments.get("description", "")

        add_custom_model(model_id, name, model_type, description)

        return [TextContent(type="text", text=f"✅ Custom model '{name}' (ID: {model_id}) added successfully!\n\nUse it with:\n- provider='zai'\n- model='{model_id}'")]

    async def run(self):
        """Run the MCP server."""
        print("Starting GLM Chatbot MCP Server...", file=sys.stderr)
        print("Available tools: send_message, analyze_image, list_models, add_custom_model", file=sys.stderr)

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                ServerCapabilities(tools=True),
            )


if __name__ == "__main__":
    server = GLMChatbotMCPServer()
    asyncio.run(server.run())
