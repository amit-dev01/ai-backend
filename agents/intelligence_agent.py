import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def run(tracking_data: dict):

    prompt = f"""
You are a competitive marketing intelligence AI.

Based on the following structured competitor data, generate a structured intelligence report.

Tracking Data:
{json.dumps(tracking_data, indent=2)}

Return ONLY valid JSON in this exact format:

{{
  "summary": "2-3 paragraph strategic summary.",
  "engagement_insights": "Explain engagement patterns and dominant platforms.",
  "pricing_insights": "Explain discount strategy and pricing positioning.",
  "campaign_insights": "Explain campaign style and messaging strategy.",
  "growth_signal": "Explain what the new launch suggests about expansion."
}}

Do not include explanations outside JSON.
Return valid JSON only.
"""

    response = model.generate_content(prompt)

    response_text = response.text.strip()

# Remove markdown code block if present
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
    if response_text.startswith("json"):
        response_text = response_text[4:]
        
        response_text = response_text.strip()

    try:
         return json.loads(response_text)
    except:
         return {"error": response_text}