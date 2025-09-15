from fastmcp import FastMCP
from typing import Dict, Any
from utils.config_loader import config_loader
from clients.api_client import api_client
import logging
import os

# 创建 FastMCP 服务器实例
mcp = FastMCP(name="api-integration-server")

@mcp.tool(name="get_all_users", 
          description="Get a list of all users from the user service"
          )
async def get_all_users() -> Dict[str, Any]:
    """
    Get all users from the user service.
    """
    try:
        result = await api_client.make_request("get_all_users")
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Fetch users failed: {str(e)}"
        }
        
        
@mcp.tool(name="get_cherrypicks_info", 
          description="cherrypicks(创奇思科技有限公司) is the name of a company. This api returns the company's policies"
          )
async def get_cherrypicks_info(query: str) -> Dict[str, Any]:
    """
    Get cherrypicks info
    """
    try:
        params ={
            "inputs": {},
            "query": query,
            # "response_mode": "streaming",
            "response_mode": "blocking",
            "conversation_id": "",
            "user": "AI_Agent",
            "files": []
        }
                    
        result = await api_client.make_request("get_cherrypicks_info", params)
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Get cherrypicks info failed: {str(e)}"
        }

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0")
    