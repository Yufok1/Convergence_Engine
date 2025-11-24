#!/usr/bin/env python3
"""
Comprehensive test script for the Convergence Engine system
Tests all major components and fixes
"""

import requests
import json
import time
import subprocess
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(name, url, method="GET", data=None, expected_status=200):
    """Test an endpoint"""
    print(f"\n🧪 Testing {name}...")
    try:
        if method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)

        if response.status_code == expected_status:
            print(f"✅ {name}: SUCCESS ({response.status_code})")
            return True, response
        else:
            print(f"❌ {name}: FAILED ({response.status_code}) - {response.text[:200]}")
            return False, response
    except Exception as e:
        print(f"❌ {name}: EXCEPTION - {e}")
        return False, None

def test_simulation():
    """Test simulation start/stop"""
    print("\n🎮 Testing Simulation Controls...")

    # Test stop first (should already be stopped)
    success1, _ = test_endpoint("Stop Simulation", f"{BASE_URL}/api/simulation/stop", "POST")

    # Test start
    success2, _ = test_endpoint("Start Simulation", f"{BASE_URL}/api/simulation/start", "POST")

    # Test status
    success3, response = test_endpoint("Simulation Status", f"{BASE_URL}/api/simulation/status")

    if success3 and response:
        status = response.json()
        print(f"   Simulation status: {status}")

    return success1 and success2 and success3

def test_graph_loading():
    """Test graph data loading"""
    print("\n📊 Testing Graph Loading...")

    success, response = test_endpoint("Graph Data", f"{BASE_URL}/api/graph")

    if success and response:
        data = response.json()
        nodes = len(data.get('nodes', []))
        links = len(data.get('links', []))
        print(f"   Loaded {nodes} nodes, {links} links")

        # Check if VP is reasonable (should be < 1.0 now)
        vp_values = [node.get('vp', 0) for node in data.get('nodes', []) if 'vp' in node]
        if vp_values:
            avg_vp = sum(vp_values) / len(vp_values)
            print(f"   Average VP: {avg_vp:.3f} (should be < 1.0)")
            if avg_vp < 1.0:
                print("   ✅ Network connectivity fix working!")
            else:
                print("   ⚠️  VP still high - network changes may need more time")

    return success

def test_ollama_config():
    """Test Ollama configuration"""
    print("\n🤖 Testing Ollama Configuration...")

    # Test config loading
    success1, response = test_endpoint("Ollama Config", f"{BASE_URL}/api/ollama/config")

    # Test model listing
    success2, response = test_endpoint("Available Models", f"{BASE_URL}/api/ollama/models")

    if success2 and response:
        models = response.json().get('models', [])
        print(f"   Found {len(models)} available models")
        vision_models = [m for m in models if 'vl' in m.lower() or 'vision' in m.lower()]
        if vision_models:
            print(f"   Vision models: {vision_models[:3]}")

    return success1 and success2

def test_vision_simulation():
    """Test vision analysis with simulated data"""
    print("\n👁️  Testing Vision Analysis...")

    # First, we need graph data to create a snapshot
    success1, graph_response = test_endpoint("Get Graph for Vision", f"{BASE_URL}/api/graph")
    if not success1 or not graph_response:
        return False

    # Create a simple test image (base64 encoded minimal PNG)
    # This is a minimal 1x1 transparent PNG in base64
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jzyr2AAAAABJRU5ErkJggg=="

    # Test vision analysis
    vision_data = {
        "image": test_image,
        "model": "qwen3-vl:235b-instruct",
        "prompt": "Describe what you see in this graph visualization."
    }

    success2, response = test_endpoint("Vision Analysis", f"{BASE_URL}/api/ollama/vision", "POST", vision_data)

    if success2 and response:
        result = response.json()
        if 'description' in result:
            desc = result['description'][:100]
            print(f"   Vision response: {desc}...")
            return True

    return success2

def main():
    """Run all tests"""
    print("🚀 Convergence Engine System Test Suite")
    print("=" * 60)

    # Wait a bit for the server to fully start
    print("⏳ Waiting for server to initialize...")
    time.sleep(3)

    # Run tests
    tests = [
        ("Simulation Controls", test_simulation),
        ("Graph Loading", test_graph_loading),
        ("Ollama Config", test_ollama_config),
        ("Vision Analysis", test_vision_simulation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}: CRASHED - {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY:")
    print("=" * 60)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print("15")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("\n🚀 Ready for evolution analysis:")
        print("   1. Start simulation")
        print("   2. Wait for graph to populate (36K+ nodes)")
        print("   3. Ask about evolution - should get 3-image timeline!")
    else:
        print("⚠️  Some systems need attention")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




