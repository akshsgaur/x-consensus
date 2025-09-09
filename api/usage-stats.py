from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.x_api_service import XAPIService
    import logging
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

    def do_GET(self):
        try:
            # CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            # Get API usage stats
            x_service = XAPIService()
            stats = x_service.get_api_usage_stats()
            
            response = {
                "success": True,
                **stats
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error in usage-stats endpoint: {e}")
            response = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(response).encode())