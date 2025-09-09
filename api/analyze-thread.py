from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.x_api_service import XAPIService
    from services.grok_service import GrokService
    from models.schemas import AnalyzeThreadRequest
    import logging
    import time
    import asyncio
except ImportError as e:
    print(f"Import error: {e}")

logger = logging.getLogger(__name__)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        return

    def do_POST(self):
        try:
            # CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Validate request
            if 'url' not in data:
                response = {"success": False, "error": "URL is required"}
                self.wfile.write(json.dumps(response).encode())
                return

            # Run async analysis
            response = asyncio.run(self.analyze_thread_async(data['url']))
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error in analyze-thread endpoint: {e}")
            response = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(response).encode())

    async def analyze_thread_async(self, url: str):
        try:
            start_time = time.time()
            
            # Initialize services
            x_service = XAPIService()
            grok_service = GrokService()
            
            # Step 1: Extract thread data
            logger.info(f"🚀 API Request: analyze-thread for URL: {url}")
            logger.info("🔍 Step 1: Extracting thread data with optimized API usage")
            
            thread_data = await x_service.extract_thread_optimized(url)
            
            api_usage = x_service.get_api_usage_stats()
            logger.info(f"📊 API Usage: {api_usage['usage_percentage']:.1f}% of monthly quota used")
            logger.info(f"✅ Step 1 Complete: Extracted {len(thread_data.tweets)} tweets from thread")
            
            # Step 2: Analyze with Grok
            logger.info("🤖 Step 2: Analyzing with Grok AI")
            consensus_response = await grok_service.analyze_thread(thread_data)
            
            processing_time = time.time() - start_time
            
            # Convert to dict for JSON serialization
            response_dict = {
                "success": True,
                "sideA": {
                    "title": consensus_response.sideA.title,
                    "points": consensus_response.sideA.points,
                    "username": consensus_response.sideA.username
                },
                "sideB": {
                    "title": consensus_response.sideB.title, 
                    "points": consensus_response.sideB.points,
                    "username": consensus_response.sideB.username
                },
                "consensus": consensus_response.consensus,
                "peace_meme_url": consensus_response.peace_meme_url,
                "meme_prompt": consensus_response.meme_prompt,
                "live_search_results": [
                    {
                        "title": result.title,
                        "url": result.url,
                        "snippet": result.snippet,
                        "relevance_score": result.relevance_score
                    } for result in (consensus_response.live_search_results or [])
                ],
                "enhanced_context": consensus_response.enhanced_context,
                "confidence_score": consensus_response.confidence_score,
                "processing_time": consensus_response.processing_time
            }
            
            logger.info(f"🎉 Successfully completed analysis for thread")
            logger.info(f"📊 Final API usage: {api_usage['usage_percentage']:.1f}% of monthly quota")
            
            return response_dict
            
        except Exception as e:
            logger.error(f"Error in thread analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }