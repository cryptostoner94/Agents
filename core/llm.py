"""
Multi-LLM Manager - OpenRouter, OpenAI, Gemini, Grok, HuggingFace, Fireworks
"""
import os
import json
import aiohttp
from typing import Optional, List, Dict
from datetime import datetime

class LLManager:
    def __init__(self):
        self.providers = {}
        self.default_model = "openrouter"
        self._init_providers()
    
    def _init_providers(self):
        """Initialize all available LLM providers"""
        # OpenRouter (primary - has multiple models)
        openrouter_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if openrouter_key:
            self.providers["openrouter"] = {
                "name": "OpenRouter",
                "api_key": openrouter_key,
                "base_url": "https://openrouter.ai/api/v1",
                "models": [
                    "anthropic/claude-3.5-sonnet",
                    "openai/gpt-4o",
                    "google/gemini-2.0-flash",
                    "meta-llama/llama-3.1-70b-instruct",
                    "mistralai/mixtral-8x7b",
                    "deepseek/deepseek-chat"
                ]
            }
        
        # Grok
        grok_key = os.getenv("GROK_API_KEY")
        if grok_key:
            self.providers["grok"] = {
                "name": "Grok",
                "api_key": grok_key,
                "base_url": "https://api.x.ai/v1",
                "models": ["grok-2-1212", "grok-2", "grok-1"]
            }
        
        # Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.providers["gemini"] = {
                "name": "Google Gemini",
                "api_key": gemini_key,
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "models": ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-pro"]
            }
        
        # HuggingFace
        hf_key = os.getenv("HUGGINGFACE_API_KEY")
        if hf_key:
            self.providers["huggingface"] = {
                "name": "HuggingFace",
                "api_key": hf_key,
                "base_url": "https://api-inference.huggingface.co/v1",
                "models": ["meta-llama/Llama-3.1-70B-Instruct", "mistralai/Mixtral-8x7B-Instruct-v0.1"]
            }
        
        # Fireworks
        fireworks_key = os.getenv("FIREWORKS_API_KEY")
        if fireworks_key:
            self.providers["fireworks"] = {
                "name": "Fireworks AI",
                "api_key": fireworks_key,
                "base_url": "https://api.fireworks.ai/inference/v1",
                "models": ["accounts/fireworks/models/llama-v3-70b-instruct"]
            }
        
        # OpenAI direct
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and "openrouter" not in self.providers:
            self.providers["openai"] = {
                "name": "OpenAI",
                "api_key": openai_key,
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
            }
    
    def get_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def list_models(self) -> Dict[str, List[str]]:
        """List all models by provider"""
        return {k: v["models"] for k, v in self.providers.items()}
    
    def is_connected(self) -> bool:
        """Check if any provider is configured"""
        return len(self.providers) > 0
    
    async def generate(self, prompt: str, model: str = "auto", **kwargs) -> str:
        """Generate response from LLM"""
        if model == "auto":
            # Use first available provider
            provider_name = list(self.providers.keys())[0]
        else:
            provider_name = self._find_provider_for_model(model)
        
        if not provider_name:
            return self._fallback_response(prompt)
        
        provider = self.providers[provider_name]
        return await self._call_api(provider, model or provider["models"][0], prompt, **kwargs)
    
    def _find_provider_for_model(self, model: str) -> Optional[str]:
        """Find which provider supports this model"""
        for name, provider in self.providers.items():
            if model in provider["models"]:
                return name
        return list(self.providers.keys())[0] if self.providers else None
    
    async def _call_api(self, provider: dict, model: str, prompt: str, **kwargs) -> str:
        """Make API call to provider"""
        try:
            headers = {
                "Authorization": f"Bearer {provider['api_key']}",
                "Content-Type": "application/json"
            }
            
            # Handle different provider formats
            if provider["name"] == "OpenRouter":
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": kwargs.get("max_tokens", 2048)
                }
            elif provider["name"] == "OpenAI":
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": kwargs.get("max_tokens", 2048)
                }
            else:
                data = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}]
                }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{provider['base_url']}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error = await resp.text()
                        return f"API Error ({resp.status}): {error[:200]}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback when no API key is configured"""
        return f"""AGENTS is ready to assist!

I've received your task: "{prompt[:100]}..."

To enable full AI capabilities, configure one of these in your .env:
- OPENROUTER_API_KEY (recommended - access to multiple models)
- OPENAI_API_KEY
- GROK_API_KEY
- GEMINI_API_KEY
- HUGGINGFACE_API_KEY
- FIREWORKS_API_KEY

Currently running in demo mode. The agent framework is operational and will process tasks once an API key is added."""

# Singleton instance
llm = LLManager()
