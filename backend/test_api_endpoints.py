import asyncio
import sys
import os

# Add current folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import paraphrase_text, humanize_text, proofread_text, TextPayload, HumanizePayload, ProofreadPayload

async def test_all():
    print("=" * 58)
    print("Testing API Endpoints")
    print("=" * 58)
    
    try:
        print("[TEST 1] Testing /api/paraphrase...")
        payload = TextPayload(text="The study shows very good results.")
        res = await paraphrase_text(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)
        
        print("[TEST 2] Testing /api/humanize (mode: noora)...")
        payload = HumanizePayload(text="Therefore, the study shows patients took many medications.", mode="noora")
        res = await humanize_text(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)

        print("[TEST 3] Testing /api/humanize (mode: general)...")
        payload = HumanizePayload(text="It stands as a testament that it is a pivotal moment.", mode="general")
        res = await humanize_text(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)
        
        print("[TEST 4] Testing /api/proofread (phase: detection)...")
        payload = ProofreadPayload(text="The study shows state-of-the-art results. It is important to delve.", phase="detection")
        res = await proofread_text(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)

        print("[TEST 5] Testing /api/proofread (phase: fix)...")
        payload = ProofreadPayload(text="The study shows state-of-the-art results. It is important to delve.", phase="fix")
        res = await proofread_text(payload)
        print("Success! Response:")
        print(res)
        print("-" * 50)
        
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_all())
