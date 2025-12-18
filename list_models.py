"""
Script to list available Gemini models for the configured API key.
Run with: python list_models.py
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ GEMINI_API_KEY not found in environment or .env file")
    exit(1)

print(f"🔑 Using API key: {api_key[:10]}...{api_key[-4:]}")

try:
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    
    print("\n📋 Available models:")
    print("=" * 60)
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"  ✅ {model.name}")
            print(f"     Display: {model.display_name}")
            print(f"     Methods: {', '.join(model.supported_generation_methods)}")
            print()
    
    print("=" * 60)
    print("\n💡 Update MODEL_NAME in your .env file to one of the models above.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPossible issues:")
    print("  1. Invalid API key")
    print("  2. API key doesn't have required permissions")
    print("  3. Network issue")
    print("\nGet a new API key from: https://makersuite.google.com/app/apikey")
