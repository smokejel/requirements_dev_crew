import os
import json
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from ..models.schemas import APIProvider, AgentConfig
import base64
import hashlib

class ConfigService:
    def __init__(self):
        self.config_dir = os.path.join(os.getcwd(), ".config")
        self.api_keys_file = os.path.join(self.config_dir, "api_keys.enc")
        self.agent_configs_file = os.path.join(self.config_dir, "agent_configs.json")
        self._ensure_config_dir()
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)
        
    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        os.makedirs(self.config_dir, exist_ok=True)
        
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for API keys"""
        key_file = os.path.join(self.config_dir, "encryption.key")
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def store_api_key(self, provider: APIProvider, api_key: str) -> bool:
        """Store encrypted API key"""
        try:
            # Load existing keys
            api_keys = self._load_encrypted_api_keys()
            
            # Encrypt and store new key
            encrypted_key = self._cipher.encrypt(api_key.encode())
            api_keys[provider.value] = base64.b64encode(encrypted_key).decode()
            
            # Save to file
            with open(self.api_keys_file, 'w') as f:
                json.dump(api_keys, f)
            
            return True
        except Exception as e:
            print(f"Error storing API key for {provider}: {e}")
            return False
    
    def get_api_key(self, provider: APIProvider) -> Optional[str]:
        """Get decrypted API key"""
        try:
            api_keys = self._load_encrypted_api_keys()
            if provider.value not in api_keys:
                return None
            
            encrypted_key = base64.b64decode(api_keys[provider.value])
            decrypted_key = self._cipher.decrypt(encrypted_key)
            return decrypted_key.decode()
        except Exception as e:
            print(f"Error retrieving API key for {provider}: {e}")
            return None
    
    def get_masked_api_key(self, provider: APIProvider) -> str:
        """Get masked API key for display"""
        api_key = self.get_api_key(provider)
        if not api_key:
            return ""
        
        if len(api_key) <= 8:
            return "*" * len(api_key)
        
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    
    def _load_encrypted_api_keys(self) -> Dict[str, str]:
        """Load encrypted API keys from file"""
        if not os.path.exists(self.api_keys_file):
            return {}
        
        try:
            with open(self.api_keys_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def validate_api_key(self, provider: APIProvider, api_key: str) -> bool:
        """Validate API key format (basic validation)"""
        if not api_key or len(api_key) < 10:
            return False
        
        # Basic format validation
        if provider == APIProvider.OPENAI:
            return api_key.startswith("sk-")
        elif provider == APIProvider.ANTHROPIC:
            return api_key.startswith("sk-ant-")
        elif provider == APIProvider.GOOGLE:
            return len(api_key) >= 20
        
        return True
    
    def store_agent_config(self, agent_name: str, config: AgentConfig) -> bool:
        """Store agent configuration"""
        try:
            configs = self._load_agent_configs()
            configs[agent_name] = config.dict()
            
            with open(self.agent_configs_file, 'w') as f:
                json.dump(configs, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error storing agent config for {agent_name}: {e}")
            return False
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get agent configuration"""
        try:
            configs = self._load_agent_configs()
            if agent_name not in configs:
                return None
            
            return AgentConfig(**configs[agent_name])
        except Exception as e:
            print(f"Error retrieving agent config for {agent_name}: {e}")
            return None
    
    def get_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations"""
        try:
            configs = self._load_agent_configs()
            return {name: AgentConfig(**config) for name, config in configs.items()}
        except Exception:
            return {}
    
    def _load_agent_configs(self) -> Dict[str, Any]:
        """Load agent configurations from file"""
        if not os.path.exists(self.agent_configs_file):
            return self._get_default_agent_configs()
        
        try:
            with open(self.agent_configs_file, 'r') as f:
                return json.load(f)
        except Exception:
            return self._get_default_agent_configs()
    
    def _get_default_agent_configs(self) -> Dict[str, Any]:
        """Get default agent configurations"""
        return {
            "requirements_analyst": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "decomposition_strategist": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "requirements_engineer": {
                "provider": "anthropic",
                "model": "claude-3-sonnet-20240229",
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "quality_assurance_agent": {
                "provider": "openai",
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "documentation_specialist": {
                "provider": "google",
                "model": "gemini-pro",
                "temperature": 0.1,
                "max_tokens": 4000
            }
        }
    
    def get_all_api_keys_masked(self) -> Dict[str, str]:
        """Get all API keys in masked format"""
        return {
            provider.value: self.get_masked_api_key(provider)
            for provider in APIProvider
        }
    
    def delete_api_key(self, provider: APIProvider) -> bool:
        """Delete API key"""
        try:
            api_keys = self._load_encrypted_api_keys()
            if provider.value in api_keys:
                del api_keys[provider.value]
                
                with open(self.api_keys_file, 'w') as f:
                    json.dump(api_keys, f)
            
            return True
        except Exception as e:
            print(f"Error deleting API key for {provider}: {e}")
            return False