#!/usr/bin/env python3
"""
Test script to demonstrate the new logging mechanisms
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.x_api_service import XAPIService

async def test_logging():
    """Test the new logging mechanisms"""
    load_dotenv()
    
    try:
        print("🧪 Testing API Logging Mechanisms")
        print("=" * 50)
        
        # Initialize the service
        x_service = XAPIService()
        print("✅ X API Service initialized successfully")
        
        # Test URL
        test_url = "https://x.com/sama/status/1964032860664582618"
        
        print(f"🔄 Testing thread extraction with detailed logging...")
        print("📋 Watch the logs below to see exactly what's happening:")
        print("-" * 50)
        
        # Extract thread data (this will show all the logging)
        thread_data = await x_service.extract_thread(test_url)
        
        print("-" * 50)
        print("✅ Thread extraction completed!")
        print(f"📊 Thread ID: {thread_data.thread_id}")
        print(f"📝 Total tweets: {len(thread_data.tweets)}")
        print(f"💬 Reply count: {thread_data.reply_count}")
        print(f"📈 Monthly usage: {x_service.monthly_usage}/100")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_logging())
    
    if success:
        print("\n✅ Logging test completed successfully!")
    else:
        print("\n❌ Logging test failed!")
        sys.exit(1)
