#!/usr/bin/env python3
"""
Simple test to check if the rate limiting improvements work
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.x_api_service import XAPIService

async def test_simple_extraction():
    """Test just the thread extraction part"""
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Simple Thread Extraction")
    print("=" * 50)
    
    success = asyncio.run(test_simple_extraction())
    
    if success:
        print("\n✅ Test passed!")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
