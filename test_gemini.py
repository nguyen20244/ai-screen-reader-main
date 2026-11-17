"""
Test Gemini API connection
"""
import requests
from config import config

def test_gemini_api():
    """Test if Gemini API is working"""
    
    if not config.gemini_api_key:
        print("❌ No Gemini API key found")
        return False
    
    print(f"🔑 Testing Gemini API key: {config.gemini_api_key[:20]}...")
    
    # Test the API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={config.gemini_api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "What is 2+2?"
            }]
        }]
    }
    
    try:
        print("🌐 Making API request...")
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Gemini API is working!")
            
            candidates = result.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    answer = parts[0].get('text', 'No answer')
                    print(f"🤖 Gemini response: {answer}")
                    return True
            
            print("⚠️ Unexpected response format")
            print(f"Response: {result}")
            return False
            
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("GEMINI API TEST")
    print("=" * 50)
    
    success = test_gemini_api()
    
    if success:
        print("\n🎉 Gemini API is ready to use!")
    else:
        print("\n💡 Possible solutions:")
        print("1. Check your API key at: https://makersuite.google.com/app/apikey")
        print("2. Make sure the key has proper permissions")
        print("3. Check if you have quota remaining")
        print("4. Try regenerating the API key")
