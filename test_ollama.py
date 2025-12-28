"""Quick test to verify Ollama connectivity and model availability."""

import requests

def test_ollama():
    url = "http://localhost:11434"
    model = "gpt-oss:120b"
    
    print("Testing Ollama connection...")
    
    # Test connection
    try:
        response = requests.get(f"{url}/api/tags")
        if response.status_code == 200:
            print("✅ Ollama is running")
            models = response.json().get("models", [])
            print(f"   Available models: {len(models)}")
            for m in models:
                print(f"   - {m['name']}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running (try: ollama serve)")
        return False
    
    # Test model
    print(f"\nTesting model: {model}")
    try:
        response = requests.post(
            f"{url}/api/generate",
            json={
                "model": model,
                "prompt": "Say 'OK' if you can read this.",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()["response"]
            print(f"✅ Model responded: {result[:100]}")
            return True
        else:
            print(f"❌ Model test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False

if __name__ == "__main__":
    success = test_ollama()
    if success:
        print("\n✅ All tests passed! Ready to process transcriptions.")
    else:
        print("\n❌ Tests failed. Please check Ollama setup.")
