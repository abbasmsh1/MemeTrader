from langchain.llms.base import LLM
from typing import Any, List, Optional
import together
from config.config import TOGETHER_API_KEY, TOGETHER_MODEL

class TogetherLLM(LLM):
    model: str = TOGETHER_MODEL
    temperature: float = 0.7
    max_tokens: int = 2000
    
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        together.api_key = TOGETHER_API_KEY
        
    @property
    def _llm_type(self) -> str:
        return "together"
        
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        response = together.Complete.create(
            prompt=prompt,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stop=stop
        )
        return response['output']['choices'][0]['text'] 