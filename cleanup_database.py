"""
Database Cleanup Script
Removes duplicate test claims from the database
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("="*60)
print("PROJECT AEGIS - DATABASE CLEANUP")
print("="*60)

# Get all claims
response = supabase.table("raw_claims").select("*").execute()
all_claims = response.data

print(f"\nTotal claims in database: {len(all_claims)}")

# Find duplicate test claims
test_claims = [
    "Breaking: Major earthquake hits city center!",
    "Scientists confirm that drinking water cures all forms of cancer",
    "New government policy will eliminate all taxes starting next month"
]

duplicate_ids = []
for claim in all_claims:
    claim_text = claim.get("claim_text", "")
    if any(test_claim in claim_text for test_claim in test_claims):
        duplicate_ids.append(claim["claim_id"])

print(f"Found {len(duplicate_ids)} duplicate test claims")

if duplicate_ids:
    print("\nDo you want to delete these duplicate claims? (yes/no)")
    choice = input("> ").strip().lower()
    
    if choice == "yes":
        # Delete from raw_claims
        for claim_id in duplicate_ids:
            try:
                supabase.table("raw_claims").delete().eq("claim_id", claim_id).execute()
                print(f"✓ Deleted claim {claim_id}")
            except Exception as e:
                print(f"✗ Error deleting claim {claim_id}: {e}")
        
        # Delete from verified_claims
        try:
            response = supabase.table("verified_claims").select("*").execute()
            verified_claims = response.data
            
            for verified in verified_claims:
                if verified["raw_claim_id"] in duplicate_ids:
                    supabase.table("verified_claims").delete().eq("verification_id", verified["verification_id"]).execute()
                    print(f"✓ Deleted verified claim {verified['verification_id']}")
        except Exception as e:
            print(f"Error cleaning verified_claims: {e}")
        
        print(f"\n✅ Cleanup complete! Deleted {len(duplicate_ids)} duplicate claims")
    else:
        print("\nCleanup cancelled")
else:
    print("\n✅ No duplicate test claims found!")

print("\n" + "="*60)
print("Database is now clean!")
print("="*60)
