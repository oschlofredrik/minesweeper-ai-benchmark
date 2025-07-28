#!/usr/bin/env python3
"""Test API key directly"""
import os
import urllib.request
import json

# Test with environment variable
api_key = os.environ.get('OPENAI_API_KEY', '')
if not api_key:
    print("No OPENAI_API_KEY found in environment")
    exit(1)

print(f"Testing API key: {api_key[:8]}...{api_key[-4:]}")

# Test direct API call
url = "https://api.openai.com/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
}

req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("✓ API key is valid!")
        print(f"Found {len(data.get('data', []))} models")
except urllib.error.HTTPError as e:
    print(f"✗ API key test failed: {e.code} {e.reason}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"✗ Error: {e}")