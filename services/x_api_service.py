import httpx
import re
import os
import asyncio
import time
from typing import List, Optional, Dict, Any
from models.schemas import Tweet, ThreadData, TwitterUser
import logging

logger = logging.getLogger(__name__)


class XAPIService:
    """Service for interacting with X/Twitter API v2"""
    
    def __init__(self):
        self.bearer_token = os.getenv("X_BEARER_TOKEN")
        if not self.bearer_token:
            raise ValueError("X_BEARER_TOKEN environment variable is required")
        
        self.base_url = "https://api.twitter.com/2"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }
        
        # Rate limiting configuration
        self.rate_limit_remaining = 10  # Very conservative for 15-min window
        self.rate_limit_reset_time = 0
        self.last_request_time = 0
        self.min_request_interval = 5.0  # 5 seconds between requests to be very safe
        self.monthly_usage = 0  # Track monthly usage
    
    def extract_thread_id(self, url: str) -> str:
        """Extract thread ID from X/Twitter URL"""
        pattern = r'https?://(twitter\.com|x\.com)/\w+/status/(\d+)'
        match = re.search(pattern, url)
        if not match:
            raise ValueError("Invalid X/Twitter URL format")
        return match.group(2)
    
    async def _wait_for_rate_limit(self):
        """Wait if we're approaching rate limits or need to space out requests"""
        current_time = time.time()
        
        # Check monthly usage limit (Free plan: 100 posts/month)
        if self.monthly_usage >= 95:  # Stop at 95 to be safe
            raise Exception("Monthly post limit nearly reached. Please wait for reset or upgrade your plan.")
        
        # Check if we need to wait for rate limit reset (15-minute window)
        if self.rate_limit_reset_time > current_time and self.rate_limit_remaining <= 2:
            wait_time = self.rate_limit_reset_time - current_time + 1
            logger.warning(f"15-minute rate limit nearly exhausted. Waiting {wait_time:.1f} seconds for reset")
            await asyncio.sleep(wait_time)
            self.rate_limit_remaining = 10  # Reset to conservative estimate
        
        # Ensure minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _update_rate_limit_info(self, response_headers: Dict[str, str]):
        """Update rate limit information from response headers"""
        if 'x-rate-limit-remaining' in response_headers:
            self.rate_limit_remaining = int(response_headers['x-rate-limit-remaining'])
        
        if 'x-rate-limit-reset' in response_headers:
            self.rate_limit_reset_time = int(response_headers['x-rate-limit-reset'])
        
        # Increment monthly usage counter (only for successful calls)
        self.monthly_usage += 1
        logger.info(f"✅ Successful API call - Monthly usage: {self.monthly_usage}/100 posts")
    
    def _parse_users_from_includes(self, includes: Dict[str, Any]) -> Dict[str, TwitterUser]:
        """Parse user data from includes array"""
        users = {}
        for user_data in includes.get("users", []):
            users[user_data["id"]] = TwitterUser(
                id=user_data["id"],
                username=user_data["username"],
                name=user_data["name"],
                profile_image_url=user_data.get("profile_image_url"),
                verified=user_data.get("verified"),
                public_metrics=user_data.get("public_metrics")
            )
        return users
    
    def _parse_referenced_tweets(self, includes: Dict[str, Any], users: Dict[str, TwitterUser]) -> Dict[str, Tweet]:
        """Parse referenced tweets from includes array"""
        referenced_tweets = {}
        for tweet_data in includes.get("tweets", []):
            user = users.get(tweet_data["author_id"])
            referenced_tweets[tweet_data["id"]] = Tweet(
                id=tweet_data["id"],
                text=tweet_data["text"],
                author_id=tweet_data["author_id"],
                author_username=user.username if user else "unknown",
                author_name=user.name if user else None,
                created_at=tweet_data["created_at"],
                public_metrics=tweet_data.get("public_metrics"),
                context_annotations=tweet_data.get("context_annotations"),
                referenced_tweets=tweet_data.get("referenced_tweets"),
                conversation_id=tweet_data.get("conversation_id")
            )
        return referenced_tweets
    
    def _categorize_tweets(self, tweets: List[Tweet], main_author_id: str) -> Dict[str, List[Tweet]]:
        """Categorize tweets into different types"""
        categories = {
            "main_thread": [],
            "quote_tweets": [],
            "replies": [],
            "other": []
        }
        
        for tweet in tweets:
            # Check if it's part of the main thread (same author)
            if tweet.author_id == main_author_id:
                categories["main_thread"].append(tweet)
            # Check if it has referenced tweets (quote tweet or reply)
            elif tweet.referenced_tweets:
                ref_types = [ref.get("type") for ref in tweet.referenced_tweets]
                if "quoted" in ref_types:
                    categories["quote_tweets"].append(tweet)
                elif "replied_to" in ref_types:
                    categories["replies"].append(tweet)
                else:
                    categories["other"].append(tweet)
            else:
                categories["other"].append(tweet)
        
        return categories
    
    async def get_thread_text_only(self, url: str) -> List[str]:
        """Ultra-lightweight method to get just the text content of tweets"""
        logger.info(f"🚀 Getting thread text only (minimal API usage)")
        
        try:
            thread_id = self.extract_thread_id(url)
            
            # Single API call optimized for text extraction only
            url_endpoint = f"{self.base_url}/tweets/search/recent"
            query = f"conversation_id:{thread_id}"
            params = {
                "query": query,
                "tweet.fields": "author_id,created_at",  # Minimal fields
                "user.fields": "username",  # Just username
                "expansions": "author_id",  # Just author expansion
                "max_results": 100
            }
            
            await self._wait_for_rate_limit()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url_endpoint, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                self._update_rate_limit_info(dict(response.headers))
            
            tweets_data = data.get("data", [])
            includes = data.get("includes", {})
            users = {user["id"]: user["username"] for user in includes.get("users", [])}
            
            # Extract just text with minimal author info
            thread_texts = []
            for tweet_data in tweets_data:
                author = users.get(tweet_data["author_id"], "unknown")
                text_entry = f"@{author}: {tweet_data['text']}"
                thread_texts.append(text_entry)
            
            # Try to get main tweet if not in results (one additional call if needed)
            main_tweet_found = any(tweet["id"] == thread_id for tweet in tweets_data)
            if not main_tweet_found:
                main_tweet = await self.get_tweet_by_id(thread_id)
                if main_tweet:
                    main_text = f"@{main_tweet.author_username}: {main_tweet.text}"
                    thread_texts.insert(0, main_text)
            
            logger.info(f"✅ Extracted {len(thread_texts)} tweet texts with minimal API usage")
            return thread_texts
            
        except Exception as e:
            logger.error(f"Error in text-only extraction: {e}")
            raise Exception(f"Failed to extract thread text: {str(e)}")
    
    async def _make_api_request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make API request with retry logic and rate limiting"""
        max_retries = 3
        base_delay = 1.0
        
        # Log the API call attempt
        logger.info(f"🚀 Starting API call: {method} {url}")
        logger.info(f"📊 Current rate limit remaining: {self.rate_limit_remaining}")
        logger.info(f"📅 Monthly usage: {self.monthly_usage}/100")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Attempt {attempt + 1}/{max_retries}")
                
                # Wait for rate limit if needed
                await self._wait_for_rate_limit()
                
                # Log the actual request
                logger.info(f"📡 Making request to: {url}")
                if 'params' in kwargs:
                    logger.info(f"📋 Request params: {kwargs['params']}")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    if method.upper() == 'GET':
                        response = await client.get(url, headers=self.headers, **kwargs)
                    else:
                        response = await client.request(method, url, headers=self.headers, **kwargs)
                    
                    # Log response details
                    logger.info(f"✅ Response received: {response.status_code}")
                    logger.info(f"📏 Response size: {len(response.content)} bytes")
                    
                    # Log rate limit headers
                    rate_limit_headers = {
                        'x-rate-limit-limit': response.headers.get('x-rate-limit-limit'),
                        'x-rate-limit-remaining': response.headers.get('x-rate-limit-remaining'),
                        'x-rate-limit-reset': response.headers.get('x-rate-limit-reset')
                    }
                    logger.info(f"⏱️ Rate limit headers: {rate_limit_headers}")
                    
                    response.raise_for_status()
                    
                    # Only count successful API calls
                    self._update_rate_limit_info(dict(response.headers))
                    
                    logger.info(f"🎉 API call successful on attempt {attempt + 1}")
                    return response
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"❌ HTTP Error {e.response.status_code}: {e}")
                logger.error(f"📄 Response content: {e.response.text[:500]}...")
                
                if e.response.status_code == 429:
                    # Rate limit exceeded - wait and retry
                    retry_after = e.response.headers.get('retry-after', '60')
                    wait_time = float(retry_after)
                    
                    # Log rate limit details
                    rate_limit_headers = {
                        'x-rate-limit-limit': e.response.headers.get('x-rate-limit-limit'),
                        'x-rate-limit-remaining': e.response.headers.get('x-rate-limit-remaining'),
                        'x-rate-limit-reset': e.response.headers.get('x-rate-limit-reset'),
                        'retry-after': e.response.headers.get('retry-after')
                    }
                    logger.error(f"⏱️ Rate limit headers: {rate_limit_headers}")
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"⏳ Rate limit exceeded (attempt {attempt + 1}/{max_retries}). Waiting {wait_time} seconds before retry")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error("💥 Rate limit exceeded after all retries")
                        raise Exception("Rate limit exceeded. Please try again later.")
                else:
                    # Other HTTP errors - don't retry
                    logger.error(f"💥 HTTP error {e.response.status_code}: {e}")
                    raise
            except Exception as e:
                logger.error(f"💥 Unexpected error: {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"🔄 Request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"💥 Max retries exceeded: {e}")
                    raise
        
        raise Exception("Max retries exceeded")
    
    async def get_tweet_by_id(self, tweet_id: str) -> Optional[Tweet]:
        """Get a single tweet by ID with enhanced fields"""
        logger.info(f"🔍 Fetching tweet by ID: {tweet_id}")
        
        url = f"{self.base_url}/tweets/{tweet_id}"
        params = {
            "tweet.fields": "created_at,author_id,public_metrics,context_annotations,conversation_id,referenced_tweets,reply_settings",
            "user.fields": "username,name,profile_image_url,verified,public_metrics",
            "expansions": "author_id,referenced_tweets.id,referenced_tweets.id.author_id"
        }
        
        try:
            response = await self._make_api_request_with_retry('GET', url, params=params)
            data = response.json()
            
            # Log detailed single tweet response
            logger.info(f"🔍 Single Tweet API Response:")
            logger.info(f"  Response Keys: {list(data.keys())}")
            
            if "data" not in data:
                logger.warning(f"⚠️ No data found for tweet ID: {tweet_id}")
                return None
            
            tweet_data = data["data"]
            logger.info(f"  📝 Main Tweet Details:")
            logger.info(f"    ID: {tweet_data['id']}")
            logger.info(f"    Author ID: {tweet_data['author_id']}")
            logger.info(f"    Text: {tweet_data['text']}")
            logger.info(f"    Created: {tweet_data.get('created_at')}")
            if tweet_data.get('referenced_tweets'):
                logger.info(f"    Referenced Tweets: {tweet_data['referenced_tweets']}")
            if tweet_data.get('public_metrics'):
                logger.info(f"    Metrics: {tweet_data['public_metrics']}")
            
            includes = data.get("includes", {})
            if includes:
                logger.info(f"  📦 Includes Keys: {list(includes.keys())}")
                if "users" in includes:
                    for user in includes["users"]:
                        logger.info(f"    👤 User: @{user['username']} ({user['name']})")
                if "tweets" in includes:
                    for ref_tweet in includes["tweets"]:
                        logger.info(f"    🐦 Referenced Tweet: {ref_tweet['id']} - {ref_tweet['text'][:60]}...")
            
            users = {user["id"]: user for user in includes.get("users", [])}
            referenced_tweets = {tweet["id"]: tweet for tweet in includes.get("tweets", [])}
            
            user = users.get(tweet_data["author_id"], {})
            
            logger.info(f"✅ Successfully fetched tweet from @{user.get('username', 'unknown')}")
            logger.info(f"📝 Tweet text preview: {tweet_data['text'][:100]}...")
            logger.info(f"📊 Referenced tweets found: {len(referenced_tweets)}")
            
            return Tweet(
                id=tweet_data["id"],
                text=tweet_data["text"],
                author_id=tweet_data["author_id"],
                author_username=user.get("username", "unknown"),
                author_name=user.get("name"),
                created_at=tweet_data["created_at"],
                public_metrics=tweet_data.get("public_metrics"),
                context_annotations=tweet_data.get("context_annotations"),
                referenced_tweets=tweet_data.get("referenced_tweets"),
                conversation_id=tweet_data.get("conversation_id")
            )
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️ Tweet not found: {tweet_id}")
                return None
            else:
                logger.error(f"💥 HTTP error getting tweet {tweet_id}: {e}")
                raise Exception(f"Failed to fetch tweet: {e}")
        except Exception as e:
            logger.error(f"💥 Error getting tweet {tweet_id}: {e}")
            raise Exception(f"Failed to fetch tweet: {e}")
    
    async def get_thread_replies(self, tweet_id: str, max_results: int = 100) -> List[Tweet]:
        """Get replies to a tweet (thread continuation)"""
        logger.info(f"🔍 Fetching thread replies for tweet: {tweet_id}")
        logger.info(f"📊 Max results requested: {max_results}")
        
        url = f"{self.base_url}/tweets/search/recent"
        query = f"conversation_id:{tweet_id}"
        params = {
            "query": query,
            "tweet.fields": "created_at,author_id,public_metrics,context_annotations,conversation_id,referenced_tweets,reply_settings",
            "user.fields": "username,name,profile_image_url,verified,public_metrics",
            "expansions": "author_id,referenced_tweets.id,referenced_tweets.id.author_id",
            "max_results": min(max_results, 100)
        }
        
        try:
            response = await self._make_api_request_with_retry('GET', url, params=params)
            data = response.json()
            
            logger.info(f"📊 Search response data keys: {list(data.keys())}")
            
            if "data" not in data:
                logger.info(f"ℹ️ No replies found for tweet: {tweet_id}")
                return []
            
            tweets_data = data["data"]
            includes = data.get("includes", {})
            users = {user["id"]: user for user in includes.get("users", [])}
            referenced_tweets = {tweet["id"]: tweet for tweet in includes.get("tweets", [])}
            
            logger.info(f"📝 Found {len(tweets_data)} replies")
            logger.info(f"👥 Found {len(users)} unique users")
            logger.info(f"📊 Referenced tweets in replies: {len(referenced_tweets)}")
            
            tweets = []
            for i, tweet_data in enumerate(tweets_data):
                user = users.get(tweet_data["author_id"], {})
                tweets.append(Tweet(
                    id=tweet_data["id"],
                    text=tweet_data["text"],
                    author_id=tweet_data["author_id"],
                    author_username=user.get("username", "unknown"),
                    author_name=user.get("name"),
                    created_at=tweet_data["created_at"],
                    public_metrics=tweet_data.get("public_metrics"),
                    context_annotations=tweet_data.get("context_annotations"),
                    referenced_tweets=tweet_data.get("referenced_tweets"),
                    conversation_id=tweet_data.get("conversation_id")
                ))
                
                # Log first few replies for debugging
                if i < 3:
                    logger.info(f"📝 Reply {i+1}: @{user.get('username', 'unknown')} - {tweet_data['text'][:50]}...")
            
            logger.info(f"✅ Successfully fetched {len(tweets)} replies")
            return tweets
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️ No replies found for tweet: {tweet_id}")
                return []
            else:
                logger.error(f"💥 HTTP error getting replies for {tweet_id}: {e}")
                raise Exception(f"Failed to fetch replies: {e}")
        except Exception as e:
            logger.error(f"💥 Error getting replies for {tweet_id}: {e}")
            raise Exception(f"Failed to fetch replies: {e}")
    
    async def extract_thread_optimized(self, url: str) -> ThreadData:
        """Extract thread data with single API call to /2/tweets endpoint"""
        logger.info(f"🚀 Starting single-call thread extraction for URL: {url}")
        
        try:
            thread_id = self.extract_thread_id(url)
            logger.info(f"📋 Extracted thread ID: {thread_id}")
            
            # Single API call to get tweet with all referenced tweets and users
            logger.info("🔍 Making single API call to /2/tweets endpoint...")
            
            api_url = f"{self.base_url}/tweets/{thread_id}"
            params = {
                "expansions": "referenced_tweets.id,referenced_tweets.id.author_id,author_id",
                "tweet.fields": "referenced_tweets,conversation_id,created_at,public_metrics,context_annotations",
                "user.fields": "name,username,verified,public_metrics,profile_image_url"
            }
            
            await self._wait_for_rate_limit()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                self._update_rate_limit_info(dict(response.headers))
            
            logger.info(f"📊 Single API call completed successfully")
            
            # Log detailed API response
            logger.info(f"🔍 Single Tweet API Response:")
            logger.info(f"  Response Keys: {list(data.keys())}")
            
            if "data" not in data:
                raise Exception("No data found in API response")
            
            main_tweet_data = data["data"]
            logger.info(f"  📝 Main Tweet:")
            logger.info(f"    ID: {main_tweet_data['id']}")
            logger.info(f"    Author ID: {main_tweet_data['author_id']}")
            logger.info(f"    Text: {main_tweet_data['text']}")
            if main_tweet_data.get('referenced_tweets'):
                logger.info(f"    Referenced Tweets: {main_tweet_data['referenced_tweets']}")
            
            includes_data = data.get("includes", {})
            if includes_data:
                logger.info(f"  📦 Includes Keys: {list(includes_data.keys())}")
                if "users" in includes_data:
                    user_list = [f"@{u['username']}" for u in includes_data['users']]
                    logger.info(f"    👥 Users ({len(includes_data['users'])}): {user_list}")
                if "tweets" in includes_data:
                    logger.info(f"    🐦 Referenced Tweets ({len(includes_data['tweets'])}):")
                    for i, ref_tweet in enumerate(includes_data['tweets']):
                        logger.info(f"      RefTweet {i+1}: {ref_tweet['id']} - {ref_tweet['text'][:80]}...")
            
            # Parse the single tweet response
            includes = data.get("includes", {})
            
            # Parse users from includes
            users = self._parse_users_from_includes(includes)
            logger.info(f"👥 Parsed {len(users)} users from includes")
            
            # Parse referenced tweets from includes  
            referenced_tweets = self._parse_referenced_tweets(includes, users)
            logger.info(f"📊 Parsed {len(referenced_tweets)} referenced tweets")
            
            # Create the main tweet object
            main_author = users.get(main_tweet_data["author_id"])
            main_tweet = Tweet(
                id=main_tweet_data["id"],
                text=main_tweet_data["text"],
                author_id=main_tweet_data["author_id"],
                author_username=main_author.username if main_author else "unknown",
                author_name=main_author.name if main_author else None,
                created_at=main_tweet_data.get("created_at"),
                public_metrics=main_tweet_data.get("public_metrics"),
                context_annotations=main_tweet_data.get("context_annotations"),
                referenced_tweets=main_tweet_data.get("referenced_tweets"),
                conversation_id=main_tweet_data.get("conversation_id")
            )
            
            # Combine main tweet with referenced tweets for full thread context
            all_tweets = [main_tweet]
            
            # Add referenced tweets as additional context
            for ref_tweet_data in includes.get("tweets", []):
                ref_author = users.get(ref_tweet_data["author_id"])
                ref_tweet = Tweet(
                    id=ref_tweet_data["id"],
                    text=ref_tweet_data["text"],
                    author_id=ref_tweet_data["author_id"],
                    author_username=ref_author.username if ref_author else "unknown",
                    author_name=ref_author.name if ref_author else None,
                    created_at=ref_tweet_data.get("created_at"),
                    public_metrics=ref_tweet_data.get("public_metrics"),
                    context_annotations=ref_tweet_data.get("context_annotations"),
                    referenced_tweets=ref_tweet_data.get("referenced_tweets"),
                    conversation_id=ref_tweet_data.get("conversation_id")
                )
                all_tweets.append(ref_tweet)
            
            # Categorize tweets by type
            categories = self._categorize_tweets(all_tweets, main_tweet.author_id)
            
            # Log single-call results
            logger.info(f"📋 Single-Call Extraction Summary:")
            logger.info(f"   - API calls made: 1 (optimized!)")
            logger.info(f"   - Main tweet: @{main_tweet.author_username}")
            logger.info(f"   - Total tweets: {len(all_tweets)}")
            logger.info(f"   - Users parsed: {len(users)}")
            logger.info(f"   - Referenced tweets: {len(referenced_tweets)}")
            logger.info(f"   - Quote tweets: {len(categories['quote_tweets'])}")
            logger.info(f"   - Referenced context: {len(all_tweets) - 1}")
            logger.info(f"   - Monthly usage: {self.monthly_usage}/100")
            
            return ThreadData(
                thread_id=thread_id,
                tweets=all_tweets,
                main_tweet=main_tweet,
                reply_count=len(referenced_tweets),  # Referenced tweets count
                users=users,
                referenced_tweets=referenced_tweets,
                quote_tweets=categories['quote_tweets'],
                reply_chain=categories['main_thread']
            )
            
        except Exception as e:
            logger.error(f"💥 Error in optimized thread extraction from {url}: {e}")
            raise Exception(f"Failed to extract thread: {str(e)}")
    
    async def extract_thread(self, url: str) -> ThreadData:
        """Extract full thread data from X/Twitter URL (optimized version)"""
        return await self.extract_thread_optimized(url)
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """Get current API usage statistics"""
        return {
            "monthly_usage": self.monthly_usage,
            "monthly_limit": 100,
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset_time": self.rate_limit_reset_time,
            "usage_percentage": round((self.monthly_usage / 100) * 100, 1)
        }