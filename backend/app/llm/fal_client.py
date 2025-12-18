"""
Fal OpenRouter LLM Client - LangChain compatible wrapper for Claude Sonnet 4.5
"""
import os
from typing import Any, List, Optional, Iterator
from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun

import fal_client

from app.config import get_settings


class FalChatModel(BaseChatModel):
    """Custom LangChain Chat Model using Fal OpenRouter API."""
    
    model: str = "anthropic/claude-sonnet-4.5"
    temperature: float = 0.7
    max_tokens: int = 4096
    fal_key: Optional[str] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        settings = get_settings()
        self.fal_key = self.fal_key or settings.fal_key
        self.model = kwargs.get("model", settings.fal_model)
        
        if self.fal_key:
            os.environ["FAL_KEY"] = self.fal_key
    
    @property
    def _llm_type(self) -> str:
        return "fal-openrouter"
    
    @property
    def _identifying_params(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    def _convert_messages_to_prompt(self, messages: List[BaseMessage]) -> tuple[str, Optional[str]]:
        """Convert LangChain messages to Fal format."""
        system_prompt = None
        prompt_parts = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_prompt = msg.content
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")
            else:
                prompt_parts.append(str(msg.content))
        
        prompt = "\n\n".join(prompt_parts)
        return prompt, system_prompt
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response using Fal OpenRouter API."""
        prompt, system_prompt = self._convert_messages_to_prompt(messages)
        
        try:
            result = fal_client.subscribe(
                "openrouter/router",
                arguments={
                    "model": self.model,
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                }
            )
            
            output_text = result.get("output", "")
            
            message = AIMessage(content=output_text)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            raise RuntimeError(f"Fal API error: {str(e)}")
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generate - falls back to sync for now."""
        return self._generate(messages, stop, run_manager, **kwargs)


@lru_cache()
def get_llm(model: Optional[str] = None, temperature: float = 0.7) -> FalChatModel:
    """Get a cached LLM instance."""
    settings = get_settings()
    return FalChatModel(
        model=model or settings.fal_model,
        temperature=temperature,
        fal_key=settings.fal_key,
    )
