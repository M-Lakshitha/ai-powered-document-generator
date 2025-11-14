"""
Groq LLM client with retry logic and rate limiting
"""
import os
import time
import asyncio
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

class GroqClient:
    """Wrapper for Groq API with retry logic"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize only once"""
        if self._initialized:
            return
        
        # Lazy import to avoid circular dependency
        from backend.config import settings
        
        self.llm = ChatGroq(
            model_name=settings.MODEL_NAME,
            api_key=settings.GROQ_API_KEY,
            temperature=settings.TEMPERATURE
        )
        self.last_request_time = 0
        self.min_request_interval = 0.1
        self._initialized = True
    
    async def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    async def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """Generate response with retry logic"""
        await self._rate_limit()
        
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.llm.invoke, 
                    messages
                )
                return response.content
            
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"LLM call failed after {max_retries} attempts: {str(e)}")
                
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("LLM generation failed")
    
    async def generate_batch(
        self, 
        prompts: list[str],
        system_message: Optional[str] = None
    ) -> list[str]:
        """Generate responses for multiple prompts in parallel"""
        tasks = [
            self.generate(prompt, system_message)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks)


# ✅ Factory function to get the singleton instance
def get_llm_client() -> GroqClient:
    """Get the singleton LLM client instance"""
    return GroqClient()


# ✅ Create module-level instance
llm_client = get_llm_client()
