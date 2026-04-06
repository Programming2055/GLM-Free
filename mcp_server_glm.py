"""MCP Server for GLM-Free Chatbot

This MCP server exposes the chatbot functionality to external MCP clients.
Run with: python -m mcp_server_glm

Or use the Claude Code MCP configuration:
{
    "mcpServers": {
        "glm-chatbot": {
            "command": "python",
            "args": ["-m", "mcp_server_glm"],
            "cwd": "/path/to/gemma"
        }
    }
}
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional
from mcp.server.models import ServerCapabilities
from mcp.server.session import ServerSession
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    ServerResult,
    CallToolRequest,
    ListToolsRequest,
    ListToolsResult,
)
from mcp.shared.session import RequestResponder

from src.hf_client import HuggingFaceGemmaClient
from src.zai_client import ZAIClient, add_custom_model, get_all_models

import json
import asyncio

# Global clients cache
_clients = {}

def get_client(provider='huggingface', model_name=None):
    """Get or create a model client."""
    cache_key = f"{provider}:{model_name or 'default'}"
    if cache_key not in _clients:
        if provider == 'huggingface':
            _clients[cache_key] = HuggingFaceGemmaClient()
        elif provider == 'zai':
            _clients[cache_key] = ZAIClient(model_name=model_name)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    return _clients[cache_key]


class GLMChatbotServer:
    """MCP Server for GLM-Free Chatbot."""

    def __init__(self):
        self.server_info = {
            "name": "glm-chatbot",
            "version": "1.0.0",
        }

    async def list_tools(self) -> ListToolsResult:
        """List available tools."""
        tools = [
            Tool(
                name="send_message",
                description="Send a text message to the chatbot and get a response",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to send"
                        },
                        "provider": {
                            "type": "string",
                            "description": "Provider to use (huggingface or zai)",
                            "enum": ["huggingface", "zai"],
                            "default": "zai"
                        },
                        "model": {
                            "type": "string",
                            "description": "Model name (for Z.AI provider)",
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
                description="Analyze an image using vision-capable models",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the image file or URL"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Question or prompt about the image",
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
                description="List all available models and providers",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="add_custom_model",
                description="Add a custom Z.AI model to the available models",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "model_id": {
                            "type": "string",
                            "description": "The model ID (e.g., glm-4.7, glm-5)"
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
                            "description": "Optional description"
                        }
                    },
                    "required": ["model_id", "name"]
                }
            ),
            Tool(
                name="chat_with_history",
                description="Send a message with conversation history",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "description": "List of message objects with role and content",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                                    "content": {"type": "string"}
                                }
                            }
                        },
                        "provider": {
                            "type": "string",
                            "description": "Provider to use",
                            "enum": ["huggingface", "zai"],
                            "default": "zai"
                        },
                        "model": {
                            "type": "string",
                            "description": "Model name",
                            "default": "glm-4.7-flash"
                        }
                    },
                    "required": ["messages"]
                }
            ),
        ]
        return ListToolsResult(tools=tools)

    async def call_tool(self, request: CallToolRequest) -> ServerResult:
        """Execute a tool call."""
        name = request.params.name
        arguments = request.params.arguments or {}

        try:
            if name == "send_message":
                return await self._send_message(arguments)
            elif name == "analyze_image":
                return await self._analyze_image(arguments)
            elif name == "list_models":
                return await self._list_models()
            elif name == "add_custom_model":
                return await self._add_custom_model(arguments)
            elif name == "chat_with_history":
                return await self._chat_with_history(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            return ServerResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")]
            )

    async def _send_message(self, arguments: dict) -> ServerResult:
        """Send a message and return the response."""
        message = arguments["message"]
        provider = arguments.get("provider", "zai")
        model = arguments.get("model", "glm-4.7-flash")
        temperature = arguments.get("temperature", 0.7)
        max_tokens = arguments.get("max_tokens", 4096)

        client = get_client(provider, model if provider == "zai" else None)

        messages = [{"role": "user", "content": message}]
        response = client.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )

        content = response.choices[0].message.content

        return ServerResult(
            content=[TextContent(type="text", text=content)]
        )

    async def _analyze_image(self, arguments: dict) -> ServerResult:
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

        client = get_client(provider, model if provider == "zai" else None)

        response = client.chat_with_image(
            text_prompt=prompt,
            image_url=image_url,
            temperature=0.7,
            max_tokens=4096
        )

        content = response.choices[0].message.content

        return ServerResult(
            content=[TextContent(type="text", text=content)]
        )

    async def _list_models(self) -> ServerResult:
        """List all available models."""
        models_info = []

        # Hugging Face
        try:
            HuggingFaceGemmaClient()
            models_info.append("**Hugging Face:**")
            models_info.append("- Gemma 4 31B (huggingface)")
        except:
            models_info.append("- Hugging Face: Not configured")

        # Z.AI models
        models_info.append("\n**Z.AI Models:**")
        all_models = get_all_models()
        for model_id, info in all_models.items():
            free_tag = " (Free)" if info.get("free") else ""
            custom_tag = " (Custom)" if info.get("custom") else ""
            models_info.append(f"- {info['name']}: {info['description']}{free_tag}{custom_tag}")

        return ServerResult(
            content=[TextContent(type="text", text="\n".join(models_info))]
        )

    async def _add_custom_model(self, arguments: dict) -> ServerResult:
        """Add a custom model."""
        model_id = arguments["model_id"]
        name = arguments["name"]
        model_type = arguments.get("model_type", "text")
        description = arguments.get("description", "")

        add_custom_model(model_id, name, model_type, description)

        return ServerResult(
            content=[TextContent(type="text", text=f"Custom model '{name}' added successfully!")]
        )

    async def _chat_with_history(self, arguments: dict) -> ServerResult:
        """Chat with conversation history."""
        messages = arguments["messages"]
        provider = arguments.get("provider", "zai")
        model = arguments.get("model", "glm-4.7-flash")

        client = get_client(provider, model if provider == "zai" else None)

        response = client.chat(messages=messages, stream=False)
        content = response.choices[0].message.content

        return ServerResult(
            content=[TextContent(type="text", text=content)]
        )


async def main():
    """Run the MCP server."""
    server = GLMChatbotServer()

    async with stdio_server(server.server_info) as (read_stream, write_stream):
        async def handle_list_tools(request: ListToolsRequest) -> ListToolsResult:
            return await server.list_tools()

        async def handle_call_tool(request: CallToolRequest) -> ServerResult:
            return await server.call_tool(request)

        session = ServerSession(
            read_stream=read_stream,
            write_stream=write_stream,
            server_info=server.server_info,
            capabilities=ServerCapabilities(tools=True),
        )

        # Handle incoming requests
        async for message in session.incoming_messages:
            if isinstance(message, ListToolsRequest):
                result = await handle_list_tools(message)
                await session.send_result(result)
            elif isinstance(message, CallToolRequest):
                result = await handle_call_tool(message)
                await session.send_result(result)


if __name__ == "__main__":
    asyncio.run(main())
