from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class APIParameter(BaseModel):
    """API Parameter Model"""
    name: str
    type: str
    description: str
    required: bool
    default: Optional[str] = None


class APIEndpoint(BaseModel):
    """API Endpoint Model"""
    name: str
    path: str
    method: str
    description: str
    tool_name: str
    headers: Optional[Dict[str, str]] = None
    parameters: Optional[List[APIParameter]] = None


class APIConfig(BaseModel):
    """API Configuration Model"""
    name: str
    base_url: str
    headers: Optional[Dict[str, str]] = None
    endpoints: List[APIEndpoint]


class ServerConfig(BaseModel):
    """Server Configuration Model"""
    name: str
    version: str
    description: str
    port: int


class ConfigModel(BaseModel):
    """Complete Configuration Model"""
    server: ServerConfig
    apis: List[APIConfig]
