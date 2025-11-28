"""List available Gemini models"""
import google.generativeai as genai

genai.configure(api_key='AIzaSyDtvoCoQdY9VFm4exJIKYUH3REnrnFOvYE')

print("Available models:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"- {model.name} (supports: {', '.join(model.supported_generation_methods)})")
