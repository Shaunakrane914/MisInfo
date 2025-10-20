"""
Reprocess a specific claim to test updated logic
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Find the "earth is flat" claim
response = supabase.table("raw_claims").select("*").ilike("claim_text", "%earth%flat%").execute()

if response.data:
    for claim in response.data:
        claim_id = claim["claim_id"]
        print(f"Found claim {claim_id}: {claim['claim_text']}")
        
        # Reset status to reprocess
        update = supabase.table("raw_claims").update({
            "status": "pending_initial_analysis"
        }).eq("claim_id", claim_id).execute()
        
        print(f"✓ Reset claim {claim_id} to pending_initial_analysis")
        print("It will be reprocessed in the next coordinator cycle (within 30 seconds)")
else:
    print("No 'earth is flat' claim found")
