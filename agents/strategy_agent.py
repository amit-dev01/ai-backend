import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def run(intelligence_data: dict):

    prompt = f"""
You are a competitive business strategy analyst.

Based on the intelligence insights below, analyze the competitor’s overall business strategy.

Intelligence Data:
{json.dumps(intelligence_data, indent=2)}

Return ONLY valid JSON in this exact format:

{{
  "market_positioning": "...",
  "target_audience": "...",
  "core_strengths": "...",
  "core_weaknesses": "...",
  "growth_strategy": "..."
}}

Return JSON only. Do not add extra text.
"""

    response = model.generate_content(prompt)

    response_text = response.text.strip()

    # Clean markdown formatting if present
    if response_text.startswith("```"):
        response_text = response_text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(response_text)
    except:
        return {"error": response_text}