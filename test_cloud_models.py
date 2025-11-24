#!/usr/bin/env python3
"""
Test Ollama Cloud models to verify they work
"""

import requests
import json

API_KEY = "bcf09f7907bb4ba4adb55677af21d4ee.6-u4k0NFmxPjzn8KpEykvMYM"
BASE_URL = "https://ollama.com"

def test_model(model_name, message="Hello", is_vision=False):
    """Test a specific model"""
    print(f"\n🧪 Testing {model_name}...")

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": message}],
        "stream": False
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if 'message' in data:
                content = data['message'].get('content', '')
                print(f"✅ SUCCESS: {content[:100]}{'...' if len(content) > 100 else ''}")
                return True
            else:
                print(f"❌ Unexpected response: {data}")
                return False
        else:
            error_data = response.json() if response.text else {}
            print(f"❌ Error: {error_data}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚀 Testing Ollama Cloud Models")
    print("=" * 50)

    # Test vision models
    print("\n👁️  VISION MODELS:")
    vision_success = test_model("qwen3-vl:235b-instruct", "Describe a simple red square")

    # Test chat models
    print("\n💬 CHAT MODELS:")
    chat1_success = test_model("gpt-oss:20b", "Hello, what can you help me with?")
    chat2_success = test_model("gpt-oss:120b", "Explain quantum computing briefly")

    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Vision (qwen3-vl:235b-instruct): {'✅' if vision_success else '❌'}")
    print(f"Chat (gpt-oss:20b): {'✅' if chat1_success else '❌'}")
    print(f"Chat (gpt-oss:120b): {'✅' if chat2_success else '❌'}")

if __name__ == "__main__":
    main()
