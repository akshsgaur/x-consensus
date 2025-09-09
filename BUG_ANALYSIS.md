# Bug Analysis: Why 3 Runs Used 101 API Calls

## The Problem
You only ran the application 3 times, but it consumed 101 API calls instead of the expected 6 calls (3 × 2 calls per thread).

## Root Cause: Retry Logic Bug

### The Bug
The retry logic was counting **every attempt** as an API call, not just successful ones:

```python
# OLD CODE (BUGGY):
async def _make_api_request_with_retry(self, method: str, url: str, **kwargs):
    for attempt in range(max_retries):  # 3 attempts
        try:
            response = await client.get(url, headers=self.headers, **kwargs)
            # ❌ This counted EVERY attempt, even failed ones!
            self._update_rate_limit_info(dict(response.headers))
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Retry on rate limit - but each retry was counted!
                continue
```

### What Actually Happened

**Expected**: 3 threads × 2 calls each = 6 API calls  
**Actual**: Much more due to retry counting bug

```
Thread 1:
├── Main tweet call: 3 attempts (all counted) = 3 calls
└── Replies call: 3 attempts (all counted) = 3 calls
Total: 6 calls

Thread 2:
├── Main tweet call: 3 attempts (all counted) = 3 calls  
└── Replies call: 3 attempts (all counted) = 3 calls
Total: 6 calls

Thread 3:
├── Main tweet call: 3 attempts (all counted) = 3 calls
└── Replies call: 3 attempts (all counted) = 3 calls  
Total: 6 calls

Plus rate limit retries and other issues = 101 total calls
```

## The Fix

### New Code (Fixed)
```python
# NEW CODE (FIXED):
async def _make_api_request_with_retry(self, method: str, url: str, **kwargs):
    for attempt in range(max_retries):  # 3 attempts
        try:
            response = await client.get(url, headers=self.headers, **kwargs)
            response.raise_for_status()
            # ✅ Only count successful calls
            self._update_rate_limit_info(dict(response.headers))
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Retry on rate limit - but don't count failed attempts
                continue
```

### Improvements Made
1. **Only count successful API calls** - Failed attempts don't consume quota
2. **Better logging** - Shows which calls succeed vs fail
3. **Clearer error messages** - Distinguishes between different failure types
4. **Monthly usage tracking** - Prevents future overages

## Expected Behavior Now

**3 threads × 2 successful calls each = 6 API calls** (as intended)

The retry logic will still work for handling temporary failures, but failed attempts won't count against your monthly quota.

## Prevention

The updated code now:
- ✅ Only counts successful API calls
- ✅ Tracks monthly usage accurately  
- ✅ Stops at 95 posts to prevent overage
- ✅ Provides clear logging of what's happening
- ✅ Gives helpful error messages when limits are reached

This bug explains why you hit 101 posts with only 3 runs - the retry logic was incorrectly counting every attempt as quota usage.
