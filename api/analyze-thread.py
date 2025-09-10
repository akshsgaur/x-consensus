import json
import os

def handler(request):
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }
    
    # Only allow POST requests
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Method not allowed. Use POST.'
            })
        }
    
    # Check for required environment variables
    missing_vars = []
    if not os.getenv('XAI_API_KEY'):
        missing_vars.append('XAI_API_KEY')
    if not os.getenv('X_BEARER_TOKEN'):
        missing_vars.append('X_BEARER_TOKEN')
    
    if missing_vars:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'success': False,
                'error': f'Missing environment variables: {", ".join(missing_vars)}. Please set them in Vercel dashboard.'
            })
        }
    
    try:
        # Parse request body
        if hasattr(request, 'json'):
            data = request.json
        else:
            data = json.loads(request.body)
        
        if 'url' not in data:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json',
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'URL is required'
                })
            }
        
        # For now, return a test response
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'success': False,
                'error': 'Analysis service is being configured. Please check back soon.'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
        }