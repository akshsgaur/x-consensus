#!/usr/bin/env python3
"""
Simple test script for X-Consensus Builder API
"""

import asyncio
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api"

async def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")

async def test_analyze_thread(url: str):
    """Test thread analysis endpoint"""
    print(f"🔍 Testing thread analysis for: {url}")
    
    payload = {"url": url}
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{API_BASE}/analyze-thread",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ Analysis successful")
                result = response.json()
                
                print(f"\n📊 Analysis Results:")
                print(f"   Side A: {result.get('sideA', {}).get('title', 'N/A')}")
                print(f"   Side B: {result.get('sideB', {}).get('title', 'N/A')}")
                print(f"   Consensus Points: {len(result.get('consensus', []))}")
                
                for i, point in enumerate(result.get('consensus', [])[:3]):
                    print(f"   {i+1}. {point}")
                    
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Raw response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Analysis error: {e}")

async def main():
    """Run all tests"""
    print("🚀 X-Consensus Builder API Test Suite")
    print("=" * 50)
    
    # Test health
    await test_health()
    print()
    
    # Test with a sample URL (you'll need to replace with a real thread)
    sample_url = "https://x.com/elonmusk/status/1234567890"  # Replace with real URL
    
    print(f"⚠️  Note: Replace the sample URL with a real X thread URL for testing")
    print(f"📝 Current test URL: {sample_url}")
    print()
    
    # Uncomment the line below and add a real URL to test
    # await test_analyze_thread(sample_url)
    
    print("✨ Test suite completed!")

if __name__ == "__main__":
    asyncio.run(main())