import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')

print(f"DEBUG: HuggingFace API token exists: {bool(HUGGINGFACE_API_TOKEN)}")
if HUGGINGFACE_API_TOKEN:
    print(f"DEBUG: Token starts with: {HUGGINGFACE_API_TOKEN[:10]}...")

# Test text
test_text = "This is a test newsletter about artificial intelligence and machine learning. The field has seen tremendous growth in recent years with new developments in large language models and computer vision."

api_url = 'https://api-inference.huggingface.co/models/facebook/bart-large-cnn'
headers = {'Authorization': f'Bearer {HUGGINGFACE_API_TOKEN}'} if HUGGINGFACE_API_TOKEN else {}
payload = {"inputs": test_text}

print(f"DEBUG: Making API request...")
try:
    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
    print(f"DEBUG: API Response status: {response.status_code}")
    print(f"DEBUG: API Response text: {response.text[:200]}...")
    
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            summary = result[0]['summary_text']
            print(f"SUCCESS: Summary generated: {summary}")
        else:
            print(f"ERROR: Unexpected API response format: {result}")
    else:
        print(f"ERROR: API Error - Status: {response.status_code}")
        
except Exception as e:
    print(f"ERROR: {e}") 