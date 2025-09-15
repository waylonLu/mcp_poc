import httpx
from typing import Dict, Any, Optional
from utils.config_loader import config_loader


class APIClient:
    """API Client Class"""
    
    def __init__(self):
        self.config_loader = config_loader
        self.client = httpx.AsyncClient()
    
    async def make_request(self, tool_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make API request based on tool name"""
        try:
            # Get endpoint configuration
            endpoint_config = self.config_loader.get_endpoint_by_tool_name(tool_name)
            api_config = endpoint_config["api_config"]
            endpoint = endpoint_config["endpoint"]
            
            # Build request URL
            url = f"{api_config['base_url']}{endpoint['path']}"
            
            # Merge headers
            headers = {}
            if api_config.get('headers'):
                headers.update(api_config['headers'])
            if endpoint.get('headers'):
                headers.update(endpoint['headers'])
            
            # Process parameters
            request_params = params or {}
            
            # Make request based on HTTP method
            method = endpoint['method'].upper()
            
            if method == 'GET':
                response = await self.client.get(url, params=request_params, headers=headers)
            elif method == 'POST':
                response = await self.client.post(url, json=request_params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Return formatted response based on tool name
            return response.json()
            
        except httpx.HTTPError as e:
            raise Exception(f"API请求失败: {str(e)}")
        except ValueError as e:
            raise Exception(f"配置错误: {str(e)}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton API client instance
api_client = APIClient()
