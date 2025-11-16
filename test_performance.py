#!/usr/bin/env python3
"""
Performance testing script for campaigns and mailboxes endpoints
"""
import asyncio
import time
import httpx
import sys

API_BASE_URL = "http://localhost:8000"

async def test_endpoint(name: str, url: str):
    """Test an endpoint and measure its performance"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(url)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    count = len(data)
                    print(f"✅ Success: {count} items returned")
                    print(f"⏱️  Time: {elapsed:.2f}s")
                    if count > 0:
                        print(f"📊 Average: {elapsed/count:.2f}s per item")
                    return {"success": True, "time": elapsed, "count": count}
                else:
                    print(f"⚠️  Unexpected response format: {type(data)}")
                    return {"success": False, "time": elapsed, "error": "Unexpected format"}
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return {"success": False, "time": elapsed, "error": f"HTTP {response.status_code}"}
    except httpx.TimeoutException:
        elapsed = time.time() - start_time
        print(f"❌ Timeout after {elapsed:.2f}s")
        return {"success": False, "time": elapsed, "error": "Timeout"}
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Error: {str(e)}")
        return {"success": False, "time": elapsed, "error": str(e)}

async def main():
    """Run performance tests"""
    print("🚀 Starting Performance Tests")
    print(f"Testing endpoints at: {API_BASE_URL}")
    
    results = {}
    
    # Test campaigns endpoint
    campaigns_result = await test_endpoint(
        "Campaigns Dashboard",
        f"{API_BASE_URL}/api/campaigns/dashboard"
    )
    results["campaigns"] = campaigns_result
    
    # Wait a bit between tests
    await asyncio.sleep(2)
    
    # Test mailboxes endpoint
    mailboxes_result = await test_endpoint(
        "Mailboxes",
        f"{API_BASE_URL}/api/mailboxes"
    )
    results["mailboxes"] = mailboxes_result
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    
    if results["campaigns"]["success"]:
        print(f"Campaigns: {results['campaigns']['time']:.2f}s ({results['campaigns']['count']} campaigns)")
    else:
        print(f"Campaigns: FAILED - {results['campaigns'].get('error', 'Unknown error')}")
    
    if results["mailboxes"]["success"]:
        print(f"Mailboxes: {results['mailboxes']['time']:.2f}s ({results['mailboxes']['count']} mailboxes)")
    else:
        print(f"Mailboxes: FAILED - {results['mailboxes'].get('error', 'Unknown error')}")
    
    total_time = results["campaigns"]["time"] + results["mailboxes"]["time"]
    print(f"\nTotal Time: {total_time:.2f}s")
    
    if results["campaigns"]["success"] and results["mailboxes"]["success"]:
        print(f"\n✅ Both endpoints completed successfully!")
        print(f"📈 Performance metrics saved above")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

