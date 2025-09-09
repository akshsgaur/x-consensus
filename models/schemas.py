from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Dict, Any
import re


class ThreadRequest(BaseModel):
    """Request model for thread analysis"""
    url: str = Field(..., description="X/Twitter thread URL")
    
    @validator('url')
    def validate_twitter_url(cls, v):
        """Validate that the URL is a valid X/Twitter thread URL"""
        # Match various Twitter/X URL formats
        pattern = r'https?://(twitter\.com|x\.com)/\w+/status/\d+'
        if not re.match(pattern, v):
            raise ValueError('Invalid X/Twitter thread URL format')
        return v


class TwitterUser(BaseModel):
    """Twitter/X user model"""
    id: str
    username: str
    name: str
    profile_image_url: Optional[str] = None
    verified: Optional[bool] = None
    public_metrics: Optional[Dict[str, int]] = None


class Tweet(BaseModel):
    """Individual tweet model"""
    id: str
    text: str
    author_id: str
    author_username: str
    author_name: Optional[str] = None
    created_at: str
    public_metrics: Optional[Dict[str, int]] = None
    context_annotations: Optional[List[Dict[str, Any]]] = None
    referenced_tweets: Optional[List[Dict[str, str]]] = None
    conversation_id: Optional[str] = None


class ThreadData(BaseModel):
    """Thread extraction response model"""
    thread_id: str
    tweets: List[Tweet]
    main_tweet: Tweet
    reply_count: int
    users: Optional[Dict[str, TwitterUser]] = Field(default_factory=dict, description="User information indexed by user ID")
    referenced_tweets: Optional[Dict[str, Tweet]] = Field(default_factory=dict, description="Referenced tweets indexed by tweet ID")
    quote_tweets: Optional[List[Tweet]] = Field(default_factory=list, description="Quote tweets in the thread")
    reply_chain: Optional[List[Tweet]] = Field(default_factory=list, description="Main reply chain from thread author")


class ViewpointSide(BaseModel):
    """Model for one side of the debate"""
    title: str = Field(..., description="Title/summary of this viewpoint")
    points: List[str] = Field(..., description="Key arguments from this side")
    username: Optional[str] = Field(None, description="Primary username representing this side")


class LiveSearchResult(BaseModel):
    """Live search result from Grok"""
    title: str
    url: str
    snippet: str
    relevance_score: Optional[float] = None


class ConsensusResponse(BaseModel):
    """Main response model for consensus analysis"""
    sideA: ViewpointSide
    sideB: ViewpointSide
    consensus: List[str] = Field(..., description="Common ground points between both sides")
    success: bool = True
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional analysis metadata")
    
    # Enhanced fields for multi-step pipeline
    peace_meme_url: Optional[str] = Field(None, description="URL to generated peace meme")
    meme_prompt: Optional[str] = Field(None, description="Prompt used for meme generation")
    live_search_results: Optional[List[LiveSearchResult]] = Field(default_factory=list, description="Live search results from Grok")
    enhanced_context: Optional[str] = Field(None, description="Additional context from live search")
    confidence_score: Optional[float] = Field(None, description="AI confidence in consensus analysis")
    processing_time: Optional[float] = Field(None, description="Total processing time in seconds")


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = "healthy"
    timestamp: str
    version: str = "1.0.0"


class ThreadExtractionRequest(BaseModel):
    """Request model for thread extraction only"""
    url: str = Field(..., description="X/Twitter thread URL")
    
    @validator('url')
    def validate_twitter_url(cls, v):
        """Validate that the URL is a valid X/Twitter thread URL"""
        pattern = r'https?://(twitter\.com|x\.com)/\w+/status/\d+'
        if not re.match(pattern, v):
            raise ValueError('Invalid X/Twitter thread URL format')
        return v


class GrokSearchRequest(BaseModel):
    """Request model for Grok Live Search"""
    query: str = Field(..., description="Search query")
    max_results: Optional[int] = Field(10, description="Maximum number of results")


class GrokImageRequest(BaseModel):
    """Request model for Grok Image generation"""
    prompt: str = Field(..., description="Image generation prompt")
    style: Optional[str] = Field("realistic", description="Image style")
    aspect_ratio: Optional[str] = Field("1:1", description="Image aspect ratio")


class ThreadExtractionResponse(BaseModel):
    """Response model for thread extraction"""
    success: bool = True
    data: Optional[ThreadData] = None
    error: Optional[str] = None