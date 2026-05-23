"""
Multi-provider AI client with automatic fallback
Supports: Mistral (primary), Gemini (fallback)
Handles rate limiting and provider rotation
"""

import os
import time
from typing import Optional, Dict, Any, List
from mistralai import Mistral
import google.generativeai as genai


class MultiProviderAIClient:
    def __init__(self):
        # Initialize Mistral
        self.mistral_key = os.getenv("MISTRAL_API_KEY")
        self.mistral_client = Mistral(api_key=self.mistral_key) if self.mistral_key else None
        
        # Initialize Gemini
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
        
        # Rate limiting tracking
        self.mistral_limit = {"rpm": 2, "requests": [], "last_reset": time.time()}
        self.gemini_limit = {"rpm": 15, "requests": [], "last_reset": time.time()}
    
    def _check_rate_limit(self, provider: str) -> bool:
        """Check if we can make a request to this provider"""
        limit_info = self.mistral_limit if provider == "mistral" else self.gemini_limit
        current_time = time.time()
        
        # Reset if minute has passed
        if current_time - limit_info["last_reset"] >= 60:
            limit_info["requests"] = []
            limit_info["last_reset"] = current_time
        
        # Remove requests older than 1 minute
        limit_info["requests"] = [
            req_time for req_time in limit_info["requests"]
            if current_time - req_time < 60
        ]
        
        # Check if under limit
        return len(limit_info["requests"]) < limit_info["rpm"]
    
    def _record_request(self, provider: str):
        """Record that we made a request"""
        limit_info = self.mistral_limit if provider == "mistral" else self.gemini_limit
        limit_info["requests"].append(time.time())
    
    def chat_complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Send chat completion request with automatic provider fallback
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional model name override
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated text response
        """
        # Try Mistral first
        if self.mistral_client and self._check_rate_limit("mistral"):
            try:
                response = self.mistral_client.chat.complete(
                    model=model or "mistral-large-latest",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                self._record_request("mistral")
                return response.choices[0].message.content
            except Exception as e:
                print(f"Mistral error: {e}, falling back to Gemini")
        
        # Fallback to Gemini
        if self.gemini_key and self._check_rate_limit("gemini"):
            try:
                model_obj = genai.GenerativeModel('gemini-2.5-flash')
                # Convert messages to Gemini format
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                response = model_obj.generate_content(prompt)
                self._record_request("gemini")
                return response.text
            except Exception as e:
                print(f"Gemini error: {e}")
                raise Exception("All AI providers failed")
        
        # If we get here, we're rate limited
        raise Exception("Rate limited on all providers. Please wait 60 seconds.")


# Global instance
ai_client = MultiProviderAIClient()
