#!/usr/bin/env python3
"""Setup script for Hugging Face Gemma project."""

import subprocess
import sys
import os


def create_venv():
    """Create virtual environment."""
    venv_path = os.path.join(os.path.dirname(__file__), "venv")

    if os.path.exists(venv_path):
        print(f"Virtual environment already exists at {venv_path}")
        return venv_path

    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    print(f"Virtual environment created at {venv_path}")
    return venv_path


def install_dependencies(venv_path):
    """Install dependencies in virtual environment."""
    if sys.platform == "win32":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")

    print("Installing dependencies...")
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    print("Dependencies installed successfully!")


def setup_env_file():
    """Create .env file if it doesn't exist."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env_example_path = os.path.join(os.path.dirname(__file__), ".env.example")

    if os.path.exists(env_path):
        print(".env file already exists")
        return

    if os.path.exists(env_example_path):
        with open(env_example_path, "r") as f:
            content = f.read()
        with open(env_path, "w") as f:
            f.write(content)
        print("Created .env file from .env.example")
        print("IMPORTANT: Edit .env and add your Hugging Face API key!")
    else:
        print("Warning: .env.example not found")


def main():
    """Run full setup."""
    print("=" * 50)
    print("Hugging Face Gemma Project Setup")
    print("=" * 50)

    # Create venv
    venv_path = create_venv()

    # Install dependencies
    install_dependencies(venv_path)

    # Setup env file
    setup_env_file()

    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Edit .env and add your HF_API_KEY")
    print("2. Activate the virtual environment:")
    if sys.platform == "win32":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("3. Run an example: python examples/vision_example.py")


if __name__ == "__main__":
    main()
