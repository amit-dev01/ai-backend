import asyncio
import os
import sys
from datetime import datetime
from database import supabase_client

def main():
    print("Fetching a company from Supabase...")
    response = supabase_client.table("companies").select("*").limit(1).execute()
    companies = response.data
    if not companies:
        print("No companies found in database!")
        return
    
    company = companies[0]
    company_id = company["id"]
    print(f"Populating Strategy Brief for company: {company['company_name']} (ID: {company_id})")
    
    mock_data = {
        "weekly_brief": "This week saw significant movement in the decentralized social media space. Several competitors are aggressively pursuing federation and custom domains, posing a direct threat to our market positioning. However, there is a distinct lack of enterprise-focused moderation tools, presenting a strong opportunity.",
        "top_threats": [
            {
                "threat": "Rapid adoption of Nostr protocol", 
                "competitor": "nos.social", 
                "urgency": "HIGH", 
                "recommendedAction": "Accelerate development of our custom protocol bridging features."
            },
            {
                "threat": "Aggressive pricing cuts", 
                "competitor": "altsocial", 
                "urgency": "MEDIUM", 
                "recommendedAction": "Highlight our premium features and superior analytics in marketing campaigns."
            }
        ],
        "opportunities": [
            {
                "opportunity": "Enterprise Moderation Gap", 
                "basis": "Competitor platforms lack robust moderation", 
                "recommendedAction": "Launch the 'Enterprise Safety Shield' feature set immediately."
            }
        ],
        "watch_list": ["nos.social", "mirlo.social", "sociano.app"],
        "strategic_recommendations": [
            "Double down on enterprise security marketing.",
            "Run a targeted ad campaign against nos.social focusing on usability.",
            "Consider pricing adjustments for the entry-level tier to stay competitive."
        ],
        "weekly_brief_generated_at": datetime.utcnow().isoformat()
    }
    
    supabase_client.table("companies").update(mock_data).eq("id", company_id).execute()
    print("Successfully generated and saved AI Strategy Brief!")

if __name__ == "__main__":
    main()
