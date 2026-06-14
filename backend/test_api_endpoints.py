import asyncio
import sys
import os

# Add current folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import handle_paraphrase, handle_humanize, handle_proofread, TextPayload, HumanizePayload, ProofreadPayload

async def test_all():
    print("==========================================================")
    print("Executing Local API Endpoint Business Logic Tests")
    print("==========================================================\n")
    
    try:
        # Test 1: Paraphrase Endpoint
        print("[TEST 1] Testing /api/paraphrase...")
        payload = TextPayload(text="The study shows very good results.")
        res = await handle_paraphrase(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)
        
        # Test 2: Humanize Endpoint (Noora Style)
        print("[TEST 2] Testing /api/humanize (mode: noora)...")
        payload = HumanizePayload(text="Therefore, the study shows patients took many medications.", mode="noora")
        res = await handle_humanize(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)

        # Test 3: Humanize Endpoint (General Anti-AI Style)
        print("[TEST 3] Testing /api/humanize (mode: general)...")
        payload = HumanizePayload(text="It stands as a testament that it is a pivotal moment.", mode="general")
        res = await handle_humanize(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)
        
        # Test 4: Proofread Endpoint (Phase 1 Detection)
        print("[TEST 4] Testing /api/proofread (phase: detection)...")
        payload = ProofreadPayload(text="The study shows state-of-the-art results. It is important to delve.", phase="detection")
        res = await handle_proofread(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)

        # Test 5: Proofread Endpoint (Phase 2 Fix)
        print("[TEST 5] Testing /api/proofread (phase: fix)...")
        payload = ProofreadPayload(text="The study shows state-of-the-art results. It is important to delve.", phase="fix")
        res = await handle_proofread(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)
        
        print("\nAll local business logic verification tests passed successfully!")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_all())
