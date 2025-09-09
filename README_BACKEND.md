# X-Consensus Builder - Backend API

A FastAPI-based backend service that analyzes heated X/Twitter debates to find surprising common ground between opposing sides using xAI's Grok.

## 🚀 Features

- **Thread Extraction**: Extract full X/Twitter thread data via X API v2
- **AI Analysis**: Use xAI Grok to identify opposing viewpoints and consensus
- **Robust Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Type Safety**: Full Pydantic model validation throughout
- **Production Ready**: Optimized for Vercel deployment with proper logging

## 📁 Project Structure

```
api/
├── main.py              # FastAPI application and endpoints
models/
├── schemas.py           # Pydantic models for validation
services/
├── x_api_service.py     # X/Twitter API integration
├── grok_service.py      # xAI Grok analysis service
utils/
├── config.py            # Configuration and logging setup
requirements.txt         # Python dependencies
vercel.json             # Vercel deployment configuration
```

## 🛠️ Setup Instructions

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Add your API keys:
```
XAI_API_KEY=your_xai_api_key_here
X_BEARER_TOKEN=your_x_bearer_token_here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Development Server

```bash
python run_dev.py
```

The API will be available at:
- **API Base**: http://localhost:8000/api/
- **Documentation**: http://localhost:8000/api/docs
- **Alternative Docs**: http://localhost:8000/api/redoc

## 📡 API Endpoints

### Health Check
```
GET /api/health
```
Returns service health status.

### Extract Thread
```
POST /api/extract-thread
Content-Type: application/json

{
  "url": "https://x.com/username/status/123456789"
}
```

### Analyze Thread (Main Endpoint)
```
POST /api/analyze-thread
Content-Type: application/json

{
  "url": "https://x.com/username/status/123456789"
}
```

**Response Format:**
```json
{
  "sideA": {
    "title": "Conservative Economic Position",
    "points": ["Argument 1", "Argument 2", "Argument 3"]
  },
  "sideB": {
    "title": "Progressive Economic Position", 
    "points": ["Argument 1", "Argument 2", "Argument 3"]
  },
  "consensus": [
    "Both sides prioritize economic stability",
    "Both want to protect working families",
    "Both agree on need for transparency"
  ],
  "success": true,
  "metadata": {
    "thread_id": "123456789",
    "total_tweets": 47,
    "analysis_timestamp": "2024-01-01T12:00:00"
  }
}
```

## 🔧 Configuration

Key configuration options in `utils/config.py`:

- **CORS Origins**: Allowed frontend domains
- **Rate Limiting**: Max tweets per thread analysis
- **Timeouts**: API request timeout settings
- **Logging**: Configurable log levels

## 🚀 Deployment

### Vercel Deployment

1. **Push to GitHub**: Ensure your code is in a GitHub repository
2. **Connect to Vercel**: Import your GitHub repo in Vercel dashboard
3. **Environment Variables**: Add your API keys in Vercel's environment settings
4. **Deploy**: Vercel will automatically deploy using the `vercel.json` configuration

### Environment Variables for Production
```
XAI_API_KEY=your_production_xai_key
X_BEARER_TOKEN=your_production_x_token
DEBUG=false
LOG_LEVEL=INFO
```

## 🛡️ Error Handling

The API implements comprehensive error handling:

- **400**: Invalid request (bad URL format, insufficient tweets)
- **401**: Invalid API keys
- **404**: Thread not found or private
- **429**: Rate limit exceeded
- **500**: Internal server error

All errors return structured JSON responses with details.

## 🧪 Testing

### Test with cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Analyze thread
curl -X POST http://localhost:8000/api/analyze-thread \
  -H "Content-Type: application/json" \
  -d '{"url": "https://x.com/elonmusk/status/1234567890"}'
```

## 📊 Monitoring

The API includes comprehensive logging:
- Request/response logging
- Service initialization
- Error tracking with full stack traces
- Performance metrics

## 🔐 Security

- CORS middleware properly configured
- Input validation with Pydantic
- Environment variable protection
- API key security best practices
- Timeout protection against hanging requests

## 📝 Development Notes

- Uses `async/await` throughout for optimal performance
- Type hints on all functions and classes
- Modular architecture with clear separation of concerns
- Production-ready logging and error handling
- Optimized for hackathon demo performance

## 🤝 Integration

The backend integrates seamlessly with the Next.js frontend. The frontend can call:

```javascript
const response = await fetch('/api/analyze-thread', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: threadUrl })
});
const result = await response.json();
```