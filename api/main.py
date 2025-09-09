from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
import logging
from datetime import datetime
from typing import Union

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import (
    ThreadRequest, 
    ConsensusResponse, 
    ErrorResponse, 
    HealthResponse,
    ThreadExtractionRequest,
    ThreadExtractionResponse
)
from services.x_api_service import XAPIService
from services.grok_service import GrokService
from utils.config import Config, setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=Config.API_TITLE,
    description=Config.API_DESCRIPTION,
    version=Config.API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
x_service = None
grok_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global x_service, grok_service
    
    try:
        # Validate configuration
        Config.validate_config()
        
        # Initialize services
        x_service = XAPIService()
        grok_service = GrokService()
        
        logger.info("Application started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            details={"path": str(request.url.path)}
        ).dict()
    )

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=Config.API_VERSION
    )

@app.get("/api/usage-stats")
async def get_usage_stats():
    """Get current X API usage statistics"""
    try:
        if not x_service:
            return {"error": "X API service not initialized"}
        
        stats = x_service.get_api_usage_stats()
        return {
            "success": True,
            **stats,
            "status": "healthy" if stats["usage_percentage"] < 90 else "warning",
            "message": f"Using {stats['usage_percentage']}% of monthly quota"
        }
            
    except Exception as e:
        logger.error(f"Usage stats error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/test-rate-limit")
async def test_rate_limit():
    """Test endpoint to check rate limiting with minimal API usage"""
    try:
        if not x_service:
            return {"error": "X API service not initialized"}
        
        stats = x_service.get_api_usage_stats()
        
        # Just return usage stats without making API call
        return {
            "success": True,
            "message": "Rate limit check completed (no API call made)",
            **stats
        }
            
    except Exception as e:
        logger.error(f"Rate limit test error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/extract-thread", response_model=ThreadExtractionResponse)
async def extract_thread(request: ThreadExtractionRequest):
    """Extract thread data from X/Twitter URL"""
    try:
        logger.info(f"Extracting thread from URL: {request.url}")
        
        if not x_service:
            raise HTTPException(status_code=500, detail="X API service not initialized")
        
        # Extract thread data
        thread_data = await x_service.extract_thread(request.url)
        
        return ThreadExtractionResponse(
            success=True,
            data=thread_data
        )
        
    except ValueError as e:
        # Validation errors (invalid URL, etc.)
        logger.warning(f"Validation error in extract_thread: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Other errors (API failures, etc.)
        logger.error(f"Error in extract_thread: {e}")
        error_message = str(e)
        
        # Determine appropriate status code based on error type
        if "Rate limit exceeded" in error_message:
            status_code = 429
        elif "not found" in error_message.lower() or "private" in error_message.lower():
            status_code = 404
        elif "Invalid API key" in error_message or "Unauthorized" in error_message:
            status_code = 401
        else:
            status_code = 500
            
        return JSONResponse(
            status_code=status_code,
            content=ThreadExtractionResponse(
                success=False,
                error=error_message
            ).dict()
        )

@app.post("/api/analyze-thread", response_model=Union[ConsensusResponse, ErrorResponse])
async def analyze_thread(request: ThreadRequest):
    """Main endpoint: Analyze X/Twitter thread to find consensus between opposing sides"""
    logger.info(f"🚀 API Request: analyze-thread for URL: {request.url}")
    
    try:
        if not x_service or not grok_service:
            logger.error("💥 Services not initialized")
            raise HTTPException(status_code=500, detail="Services not initialized")
        
        # Step 1: Extract thread data (optimized to minimize API calls)
        logger.info("🔍 Step 1: Extracting thread data with optimized API usage")
        thread_data = await x_service.extract_thread(request.url)
        
        # Log API usage after extraction
        usage_stats = x_service.get_api_usage_stats()
        logger.info(f"📊 API Usage: {usage_stats['usage_percentage']}% of monthly quota used")
        logger.info(f"🚀 Using optimized single-call approach to /2/tweets endpoint")
        
        # Validate thread has enough content
        if len(thread_data.tweets) < 2:
            logger.warning(f"⚠️ Thread has only {len(thread_data.tweets)} tweets, need at least 2")
            raise HTTPException(
                status_code=400, 
                detail="Thread must have at least 2 tweets for meaningful analysis"
            )
        
        logger.info(f"✅ Step 1 Complete: Extracted {len(thread_data.tweets)} tweets from thread")
        
        # Step 2: Analyze with Grok
        logger.info("🤖 Step 2: Analyzing with Grok AI")
        consensus_response = await grok_service.analyze_thread(thread_data)
        
        # Add metadata
        consensus_response.metadata.update({
            "thread_url": request.url,
            "thread_id": thread_data.thread_id,
            "total_tweets": len(thread_data.tweets),
            "analysis_timestamp": datetime.utcnow().isoformat()
        })
        
        # Final usage logging
        final_stats = x_service.get_api_usage_stats()
        consensus_response.metadata.update({
            "api_usage_stats": final_stats,
            "api_calls_this_analysis": 1  # Optimized to single call per analysis
        })
        
        logger.info(f"🎉 Successfully completed analysis for thread {thread_data.thread_id}")
        logger.info(f"📊 Final API usage: {final_stats['usage_percentage']}% of monthly quota")
        logger.info(f"🔍 API calls made for this analysis: 1-2 (optimized)")
        
        return consensus_response
        
    except ValueError as e:
        # Validation errors (invalid URL, etc.)
        logger.warning(f"Validation error in analyze_thread: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Other errors (API failures, etc.)
        logger.error(f"Error in analyze_thread: {e}")
        error_message = str(e)
        
        # Determine appropriate status code based on error type
        if "Rate limit exceeded" in error_message:
            status_code = 429
        elif "not found" in error_message.lower() or "private" in error_message.lower():
            status_code = 404
        elif "Invalid API key" in error_message or "Unauthorized" in error_message:
            status_code = 401
        else:
            status_code = 500
            
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                error=error_message,
                error_code=f"HTTP_{status_code}",
                details={
                    "url": request.url,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ).dict()
        )

@app.get("/api/")
async def root():
    """Root endpoint"""
    return {
        "message": "X-Consensus Builder API",
        "version": Config.API_VERSION,
        "docs": "/api/docs",
        "endpoints": {
            "health": "/api/health",
            "usage_stats": "/api/usage-stats",
            "extract_thread": "/api/extract-thread", 
            "analyze_thread": "/api/analyze-thread",
            "test_rate_limit": "/api/test-rate-limit"
        }
    }

# For Vercel deployment
handler = app