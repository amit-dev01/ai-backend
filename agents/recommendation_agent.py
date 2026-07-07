import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def run(strategy_data: dict):

    prompt = f"""
You are a competitive growth strategist.

Based on the competitor strategy below, generate structured competitive recommendations.

The recommendations MUST include:

1. Counter Campaign Strategy
2. Positioning Strategy
3. Pricing Strategy
4. Content Opportunity

Competitor Strategy:
{json.dumps(strategy_data, indent=2)}

Assume we are a competing fitness supplement brand.

Return ONLY valid JSON in this exact format:

{{
  "counter_campaign_strategy": "...",
  "positioning_strategy": "...",
  "pricing_strategy": "...",
  "content_opportunity": "..."
}}

Return JSON only. No extra commentary.
"""

    response = model.generate_content(prompt)

    response_text = response.text.strip()

    # Clean markdown if wrapped
    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(response_text)
    except:
        return {"error": response_text}