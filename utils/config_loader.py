import yaml
from typing import Dict, Any
from pathlib import Path
from schemas.models import ConfigModel
import re
import os

class ConfigLoader:
    """Configuration Loader Class"""
    
    def __init__(self, config_path: str = "config/api_config.yaml"):
        self.config_path = Path(config_path)
        self.config: ConfigModel = None
    
    def load_config(self) -> ConfigModel:
        """Load and validate configuration file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file does not exist: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as file:
            raw_yaml = file.read()
            for key, value in os.environ.items():
                placeholder = f"${{{key}}}"  # 匹配 ${VAR_NAME} 格式
                raw_yaml = raw_yaml.replace(placeholder, value)
                
            config_data = yaml.safe_load(raw_yaml)
        
        # 验证配置数据
        self.config = ConfigModel(**config_data)
        return self.config
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        if self.config is None:
            self.load_config()
        return self.config.server.model_dump()
    
    def get_api_configs(self) -> Dict[str, Any]:
        """Get all API configurations"""
        if self.config is None:
            self.load_config()
        return {api.name: api.model_dump() for api in self.config.apis}
    
    def get_endpoint_by_tool_name(self, tool_name: str) -> Dict[str, Any]:
        """Find endpoint configuration by tool name"""
        if self.config is None:
            self.load_config()
        
        for api_config in self.config.apis:
            for endpoint in api_config.endpoints:
                if endpoint.tool_name == tool_name:
                    return {
                        "api_config": api_config.model_dump(),
                        "endpoint": endpoint.model_dump()
                    }
        
        raise ValueError(f"No endpoint found for tool name: {tool_name}")


# Singleton configuration loader instance
config_loader = ConfigLoader()
