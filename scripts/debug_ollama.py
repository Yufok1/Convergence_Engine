#!/usr/bin/env python3
"""
Debug script for Ollama API issues
"""

import json
import requests
import base64
from PIL import Image
import io

def test_api_key():
    """Test if API key is valid"""
    with open('data/causation_explorer/ollama_config.json', 'r') as f:
        config = json.load(f)

    api_key = config.get('api_key', '')
    print(f"API key length: {len(api_key)}")
    print(f"API key starts with: {api_key[:10]}...")
    print(f"API key ends with: ...{api_key[-10:]}")

    # Test basic API call
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(
            'https://ollama.com/api/chat',
            headers=headers,
            json={
                "model": "llama3.2",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            },
            timeout=10
        )

        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✅ API key is valid!")
            return True
        else:
            print(f"❌ API error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_vision_compression():
    """Test image compression for vision model"""
    # Create a test image
    img = Image.new('RGB', (800, 600), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    original_data = base64.b64encode(buffer.getvalue()).decode()

    original_size_kb = len(original_data.encode('utf-8')) / 1024
    print(f"Original image size: {original_size_kb:.1f}KB")

    # Test compression
    target_size_kb = 40
    if original_size_kb > target_size_kb:
        # Compress the image
        compressed_img = img.resize((400, 300), Image.LANCZOS)
        buffer = io.BytesIO()
        compressed_img.save(buffer, format='JPEG', quality=75)
        compressed_data = base64.b64encode(buffer.getvalue()).decode()

        compressed_size_kb = len(compressed_data.encode('utf-8')) / 1024
        print(f"Compressed image size: {compressed_size_kb:.1f}KB (target: {target_size_kb}KB)")

        return compressed_data
    else:
        print("No compression needed")
        return original_data

if __name__ == "__main__":
    print("🔍 Ollama API Debug Tool")
    print("=" * 50)

    print("\n1. Testing API Key...")
    api_ok = test_api_key()

    print("\n2. Testing Image Compression...")
    test_vision_compression()

    if api_ok:
        print("\n✅ API key is working correctly")
    else:
        print("\n❌ API key issues detected")
