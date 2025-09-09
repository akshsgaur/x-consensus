import httpx
import json
import os
import time
from typing import List, Dict, Any, Optional
from models.schemas import ThreadData, ConsensusResponse, ViewpointSide, LiveSearchResult
import logging

try:
    from xai_sdk import Client as XAIClient
except ImportError:
    XAIClient = None
    logging.warning("xAI SDK not installed, image generation will be disabled")

logger = logging.getLogger(__name__)


class GrokService:
    """Service for interacting with xAI Grok API"""
    
    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable is required")
        
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.model = "grok-3-mini"
        self.search_model = "grok-3-mini"  # Use same model for search
        self.image_model = "grok-2-image"  # Correct xAI image model
        
        # Initialize xAI client for image generation
        self.xai_client = XAIClient(api_key=self.api_key) if XAIClient else None
    
    def create_analysis_prompt(self, thread_data: ThreadData) -> str:
        """Create a comprehensive prompt for Grok to analyze the thread"""
        
        # Format tweets for analysis
        tweets_text = []
        for i, tweet in enumerate(thread_data.tweets[:50]):  # Limit to 50 tweets to avoid token limits
            tweets_text.append(f"{i+1}. @{tweet.author_username}: {tweet.text}")
        
        tweets_formatted = "\n".join(tweets_text)
        
        prompt = f"""
You are analyzing a heated X/Twitter debate to find surprising common ground between opposing sides. 

THREAD DATA:
Main Tweet: {thread_data.main_tweet.text}
Total Tweets: {len(thread_data.tweets)}

TWEETS:
{tweets_formatted}

ANALYSIS TASK:
1. Identify the two primary opposing viewpoints in this debate
2. Cluster the tweets into Side A and Side B based on their stance
3. Extract the core arguments from each side
4. Most importantly: Find GENUINE common ground - shared values, concerns, or facts that both sides actually agree on, even if they disagree on solutions

RESPONSE FORMAT (JSON only):
{{
    "sideA": {{
        "title": "Clear, neutral title for Side A's position",
        "points": ["Key argument 1", "Key argument 2", "Key argument 3"],
        "username": "primaryusername" // Most representative @username for this side (without @)
    }},
    "sideB": {{
        "title": "Clear, neutral title for Side B's position", 
        "points": ["Key argument 1", "Key argument 2", "Key argument 3"],
        "username": "otherusername" // Most representative @username for this side (without @)
    }},
    "consensus": [
        "Specific shared value/concern both sides agree on",
        "Another genuine point of agreement",
        "Third area of common ground"
    ]
}}

IMPORTANT GUIDELINES:
- Focus on GENUINE consensus, not superficial platitudes
- Look for shared underlying values even when solutions differ
- Be specific and concrete in identifying common ground
- Avoid generic statements like "both sides want what's best"
- Find the deeper human concerns both sides share
- Return ONLY the JSON response, no additional text

Analyze this debate now:
"""
        return prompt
    
    async def call_grok_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to xAI Grok"""
        logger.info(f"🤖 GROK ANALYSIS PROMPT ({len(prompt)} chars):")
        logger.info(f"{'='*50}")
        logger.info(prompt)
        logger.info(f"{'='*50}")
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": self.model,
            "stream": False,
            "temperature": 0.3,  # Lower temperature for more consistent analysis
            "max_tokens": 1500
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                if "choices" not in data or not data["choices"]:
                    raise Exception("No response from Grok API")
                
                content = data["choices"][0]["message"]["content"]
                return content
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling Grok API: {e}")
                if e.response.status_code == 429:
                    raise Exception("Rate limit exceeded. Please try again later.")
                elif e.response.status_code == 401:
                    raise Exception("Invalid API key")
                else:
                    raise Exception(f"API error: {e}")
            except Exception as e:
                logger.error(f"Error calling Grok API: {e}")
                raise Exception(f"Failed to analyze with Grok: {str(e)}")
    
    async def grok_live_search(self, query: str, max_results: int = 5) -> List[LiveSearchResult]:
        """Perform live search using Grok with web access"""
        logger.info(f"🔍 Performing live search: {query}")
        
        search_prompt = f"""
You have access to real-time web search. Please search for current information about: {query}

Provide a JSON response with search results in this format:
{{
    "results": [
        {{
            "title": "Article/page title",
            "url": "https://example.com",
            "snippet": "Brief description of the content",
            "relevance_score": 0.9
        }}
    ]
}}

Limit to {max_results} most relevant results. Focus on recent, authoritative sources.
"""
        
        logger.info(f"🔍 LIVE SEARCH PROMPT ({len(search_prompt)} chars):")
        logger.info(f"{'-'*30}")
        logger.info(search_prompt)
        logger.info(f"{'-'*30}")
        
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": search_prompt
                }
            ],
            "model": self.search_model,
            "stream": False,
            "temperature": 0.1,
            "max_tokens": 2000,
            "tools": [{
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                }
            }]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Parse search results
                results = []
                try:
                    # Extract JSON from response
                    start_idx = content.find("{")
                    end_idx = content.rfind("}") + 1
                    if start_idx != -1 and end_idx != -1:
                        json_str = content[start_idx:end_idx]
                        search_data = json.loads(json_str)
                        
                        for result in search_data.get("results", [])[:max_results]:
                            results.append(LiveSearchResult(
                                title=result.get("title", ""),
                                url=result.get("url", ""),
                                snippet=result.get("snippet", ""),
                                relevance_score=result.get("relevance_score", 0.5)
                            ))
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Could not parse search results: {e}")
                    # Fallback to mock results for now
                    results = [
                        LiveSearchResult(
                            title="Live Search Result (Demo)",
                            url="https://example.com",
                            snippet=f"Search results for: {query}",
                            relevance_score=0.8
                        )
                    ]
                
                logger.info(f"✅ Found {len(results)} search results")
                return results
                
        except Exception as e:
            logger.error(f"Live search failed: {e}")
            # Return empty results on failure
            return []
    
    async def generate_peace_meme(self, consensus_points: List[str], side_a_title: str, side_b_title: str, side_a_username: str = None, side_b_username: str = None) -> Optional[str]:
        """Generate a peace meme using xAI SDK"""
        logger.info("🎨 Generating peace meme")
        
        if not self.xai_client:
            logger.warning("xAI SDK not available, skipping image generation")
            return None
        
        # Create short meme prompt with celebrity personas (under 1024 chars)
        personas = ""
        if side_a_username and side_b_username:
            personas = f"Show @{side_a_username} and @{side_b_username} as cartoon characters or caricatures "
        
        shared_values = ', '.join(consensus_points[:2])  # Limit to 2 points to keep short
        
        meme_prompt = f"""Create a peaceful meme celebrating common ground. {personas}finding agreement on: {shared_values}. Style: Modern, clean, positive. Elements: Handshake, bridge, or unity symbols. Text: "Finding Common Ground". Avoid controversy."""
        
        # Ensure under 1024 character limit
        if len(meme_prompt) > 1024:
            meme_prompt = f"""Peace meme: {personas}agreeing on {consensus_points[0][:50]}. Clean, positive style with unity symbols."""
        
        logger.info(f"🎨 PEACE MEME PROMPT ({len(meme_prompt)} chars):")
        logger.info(f"{'-'*20}")
        logger.info(meme_prompt)
        logger.info(f"{'-'*20}")
        
        try:
            # Use xAI SDK for image generation
            response = self.xai_client.image.sample(
                model=self.image_model,
                prompt=meme_prompt.strip(),
                image_format="url"
            )
            
            if hasattr(response, 'url') and response.url:
                logger.info("✅ Peace meme generated successfully")
                return response.url
            else:
                logger.warning("No URL in xAI image response")
                return None
                
        except Exception as e:
            logger.error(f"xAI image generation failed: {e}")
            return None
    
    def create_enhanced_prompt(self, thread_data: ThreadData, live_context: str = "") -> str:
        """Create enhanced analysis prompt with live search context"""
        
        # Format tweets for analysis
        tweets_text = []
        for i, tweet in enumerate(thread_data.tweets[:50]):
            tweets_text.append(f"{i+1}. @{tweet.author_username}: {tweet.text}")
        
        tweets_formatted = "\n".join(tweets_text)
        
        context_section = ""
        if live_context:
            context_section = f"""

LIVE CONTEXT (Current Information):
{live_context}

Use this current context to inform your analysis and ensure the consensus points are relevant to the current situation.
"""
        
        prompt = f"""
You are analyzing a heated X/Twitter debate to find surprising common ground between opposing sides.

THREAD DATA:
Main Tweet: {thread_data.main_tweet.text}
Total Tweets: {len(thread_data.tweets)}

TWEETS:
{tweets_formatted}{context_section}

ANALYSIS TASK:
1. Identify the two primary opposing viewpoints in this debate
2. Cluster the tweets into Side A and Side B based on their stance
3. Extract the core arguments from each side
4. Find GENUINE common ground - shared values, concerns, or facts that both sides agree on
5. Provide confidence score for your analysis

RESPONSE FORMAT (JSON only):
{{
    "sideA": {{
        "title": "Clear, neutral title for Side A's position",
        "points": ["Key argument 1", "Key argument 2", "Key argument 3"],
        "username": "primaryusername" // Most representative @username for this side (without @)
    }},
    "sideB": {{
        "title": "Clear, neutral title for Side B's position", 
        "points": ["Key argument 1", "Key argument 2", "Key argument 3"],
        "username": "otherusername" // Most representative @username for this side (without @)
    }},
    "consensus": [
        "Specific shared value/concern both sides agree on",
        "Another genuine point of agreement",
        "Third area of common ground"
    ],
    "confidence_score": 0.85,
    "meme_prompt_suggestion": "Brief suggestion for a peace meme that celebrates this common ground"
}}

IMPORTANT GUIDELINES:
- Focus on GENUINE consensus, not superficial platitudes
- Look for shared underlying values even when solutions differ
- Be specific and concrete in identifying common ground
- Use live context to ensure relevance
- Return ONLY the JSON response, no additional text

Analyze this debate now:
"""
        return prompt
    
    def parse_grok_response(self, response_content: str) -> ConsensusResponse:
        """Parse Grok's response into structured format"""
        try:
            # Try to extract JSON from response
            # Sometimes the model might include extra text, so we need to find the JSON
            response_content = response_content.strip()
            
            # Find JSON block
            if response_content.startswith("```json"):
                response_content = response_content[7:]  # Remove ```json
            if response_content.endswith("```"):
                response_content = response_content[:-3]  # Remove ```
            
            # Try to find JSON in the response
            start_idx = response_content.find("{")
            end_idx = response_content.rfind("}") + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_content[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
            
            # Validate required fields
            required_fields = ["sideA", "sideB", "consensus"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create response object
            side_a = ViewpointSide(
                title=data["sideA"]["title"],
                points=data["sideA"]["points"],
                username=data["sideA"].get("username")
            )
            
            side_b = ViewpointSide(
                title=data["sideB"]["title"], 
                points=data["sideB"]["points"],
                username=data["sideB"].get("username")
            )
            
            # Extract additional fields if available
            confidence_score = data.get("confidence_score", 0.8)
            meme_suggestion = data.get("meme_prompt_suggestion", "")
            
            return ConsensusResponse(
                sideA=side_a,
                sideB=side_b,
                consensus=data["consensus"],
                success=True,
                confidence_score=confidence_score,
                metadata={
                    "analysis_method": "grok-3-mini",
                    "tweet_count": len(data.get("tweets_analyzed", [])),
                    "meme_suggestion": meme_suggestion
                }
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response: {response_content}")
            raise Exception("Failed to parse Grok response as JSON")
        except KeyError as e:
            logger.error(f"Missing required field in response: {e}")
            raise Exception(f"Invalid response format: missing {e}")
        except Exception as e:
            logger.error(f"Error parsing Grok response: {e}")
            raise Exception(f"Failed to parse analysis results: {str(e)}")
    
    async def analyze_thread(self, thread_data: ThreadData) -> ConsensusResponse:
        """Multi-step enhanced analysis with live search and meme generation"""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting enhanced Grok analysis for thread {thread_data.thread_id}")
            
            # Step 1: Extract key topics for live search
            main_topic = thread_data.main_tweet.text[:100]  # Use first 100 chars as search query
            search_query = f"current news {main_topic}"
            
            # Step 2: Perform live search for current context (optional enhancement)
            logger.info("🔍 Step 1: Performing live search for context")
            live_results = await self.grok_live_search(search_query, max_results=3)
            
            # Create enhanced context from search results
            live_context = ""
            if live_results:
                context_parts = []
                for result in live_results:
                    context_parts.append(f"- {result.title}: {result.snippet}")
                live_context = "\n".join(context_parts)
            
            # Step 3: Create enhanced analysis prompt
            logger.info("🧾 Step 2: Creating enhanced analysis prompt")
            prompt = self.create_enhanced_prompt(thread_data, live_context)
            
            # Step 4: Call Grok API for analysis
            logger.info("🤖 Step 3: Analyzing with Grok AI")
            grok_response = await self.call_grok_api(prompt)
            
            # Step 5: Parse response
            logger.info("📊 Step 4: Parsing analysis results")
            consensus_response = self.parse_grok_response(grok_response)
            
            # Step 6: Generate peace meme (async)
            logger.info("🎨 Step 5: Generating peace meme")
            meme_url = await self.generate_peace_meme(
                consensus_response.consensus,
                consensus_response.sideA.title,
                consensus_response.sideB.title,
                consensus_response.sideA.username,
                consensus_response.sideB.username
            )
            
            # Step 7: Enhance response with additional data
            processing_time = time.time() - start_time
            
            # Update response with enhanced fields
            consensus_response.live_search_results = live_results
            consensus_response.enhanced_context = live_context if live_context else None
            consensus_response.peace_meme_url = meme_url
            consensus_response.meme_prompt = f"Peace meme celebrating common ground between {consensus_response.sideA.title} and {consensus_response.sideB.title}"
            consensus_response.processing_time = round(processing_time, 2)
            consensus_response.confidence_score = 0.85  # Default confidence, could be extracted from parsed response
            
            # Update metadata
            consensus_response.metadata.update({
                "analysis_method": "enhanced-multi-step",
                "live_search_enabled": len(live_results) > 0,
                "meme_generated": meme_url is not None,
                "steps_completed": 6,
                "processing_time_seconds": processing_time
            })
            
            logger.info(f"✅ Enhanced analysis completed in {processing_time:.2f}s")
            logger.info(f"   - Live search results: {len(live_results)}")
            logger.info(f"   - Meme generated: {'Yes' if meme_url else 'No'}")
            logger.info(f"   - Consensus points found: {len(consensus_response.consensus)}")
            
            return consensus_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"💥 Error in enhanced analysis after {processing_time:.2f}s: {e}")
            raise Exception(f"Failed to analyze thread: {str(e)}")