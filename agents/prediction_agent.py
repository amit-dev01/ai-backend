import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def run(intelligence_data: dict):

    prompt = f"""
You are a market trend prediction AI specializing in D2C brands.

Based on the competitor intelligence insights below, predict their likely future moves.

Intelligence Data:
{json.dumps(intelligence_data, indent=2)}

Return ONLY valid JSON in this exact format:

{{
  "likely_next_move": "...",
  "future_product_direction": "...",
  "marketing_trend_shift": "...",
  "threat_level": "Low / Medium / High"
}}

Return JSON only. No extra commentary.
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