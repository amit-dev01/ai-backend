import asyncio
import os
import sys
import logging
from database import supabase_client

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def main():
    print("Fetching a company from Supabase...")
    response = supabase_client.table("companies").select("*").limit(1).execute()
    companies = response.data
    if not companies:
        print("No companies found in database!")
        return
    
    company = companies[0]
    company_id = company["id"]
    print(f"Found company: {company['company_name']} (ID: {company_id})")
    
    # Reset status
    print("Resetting setup_status to PENDING...")
    supabase_client.table("companies").update({"setup_status": "PENDING"}).eq("id", company_id).execute()
    
    print("Running discovery service directly...")
    try:
        from discovery_service import CompetitorDiscoveryService
        service = CompetitorDiscoveryService(company_id)
        await service.run()
        print("Discovery service run() finished successfully.")
    except Exception as e:
        import traceback
        print("Discovery service FAILED with exception:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
