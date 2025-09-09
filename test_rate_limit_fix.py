#!/usr/bin/env python3
"""
Test script to verify the rate limiting improvements
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.x_api_service import XAPIService

async def test_rate_limit_handling():
    """Test the rate limiting improvements"""
    load_dotenv()
    
    try:
        # Initialize the service
        x_service = XAPIService()
        print("✅ X API Service initialized successfully")
        
        # Test URL (the one that was failing)
        test_url = "https://x.com/sama/status/1964032860664582618"
        
        print(f"🔄 Testing thread extraction for: {test_url}")
        print("⏳ This may take a moment due to rate limiting...")
        
        # Extract thread data
        thread_data = await x_service.extract_thread(test_url)
        
        print("✅ Thread extraction successful!")
        print(f"📊 Thread ID: {thread_data.thread_id}")
        print(f"📝 Total tweets: {len(thread_data.tweets)}")
        print(f"💬 Reply count: {thread_data.reply_count}")
        
        # Show first few tweets
        print("\n📋 First few tweets:")
        for i, tweet in enumerate(thread_data.tweets[:3]):
            print(f"  {i+1}. @{tweet.author_username}: {tweet.text[:100]}...")
        
        print(f"\n🎉 Rate limiting improvements are working!")
        print(f"📈 Rate limit remaining: {x_service.rate_limit_remaining}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing Rate Limit Fixes")
    print("=" * 50)
    
    success = asyncio.run(test_rate_limit_handling())
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
