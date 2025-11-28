"""Test Gemini API call"""
import google.generativeai as genai
import asyncio

genai.configure(api_key='AIzaSyDtvoCoQdY9VFm4exJIKYUH3REnrnFOvYE')

async def test_async():
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    response = await model.generate_content_async('Say hello in one sentence')
    print('Async Response:', response.text)

asyncio.run(test_async())
