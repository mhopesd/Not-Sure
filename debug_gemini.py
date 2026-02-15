from google import genai
import configparser
import os

config = configparser.ConfigParser()
config.read('audio_config.ini')

try:
    raw_key = config['API_KEYS'].get('gemini', '')
    key = raw_key.strip().replace('"', '').replace("'", "")
    
    print(f"Using Key (masked): {key[:5]}...{key[-5:]}")
    
    client = genai.Client(api_key=key)
    
    print("Attempting to list models...")
    # Try to list models
    for m in client.models.list():
        print(f"Model: {m.name}")
        
    print("\nAttempting generate_content with 'gemini-1.5-flash'...")
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents='Hello, are you working?'
    )
    print(f"Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")
