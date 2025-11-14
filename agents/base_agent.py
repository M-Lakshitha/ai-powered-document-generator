from abc import ABC, abstractmethod
from typing import Dict

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, role: str, goal: str, backstory: str):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        # ✅ Import lazily to avoid circular dependency
        self._llm = None
    
    @property
    def llm(self):
        """Lazy load LLM client"""
        if self._llm is None:
            from backend.utils.llm_client import llm_client
            self._llm = llm_client
        return self._llm
    
    @abstractmethod
    async def execute(self, input_data: Dict, context: Dict) -> Dict:
        """Execute agent's main task"""
        pass
    
    def _create_system_message(self) -> str:
        """Create system message from role and backstory"""
        return f"""You are a {self.role}.

Goal: {self.goal}

Background: {self.backstory}

Provide clear, professional, and comprehensive responses."""
    
    async def _generate(self, prompt: str) -> str:
        """Generate response using LLM"""
        system_msg = self._create_system_message()
        return await self.llm.generate(prompt, system_msg)
    
    async def llm_call(self, prompt: str) -> str:
        """Alias for _generate for backward compatibility"""
        return await self._generate(prompt)