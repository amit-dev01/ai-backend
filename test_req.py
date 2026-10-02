import urllib.request
import json

data = {
  "company_name": "Example",
  "website_url": "https://example.com",
  "industry": "Internet",
  "our_company_context": "We do things.",
  "social_urls": {},
  "focus_areas": []
}

req = urllib.request.Request(
    'http://localhost:8000/analyze',
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        print(response.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
