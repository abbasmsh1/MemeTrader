from crewai import LLM
from config.config import TOGETHER_API_KEY

class TogetherLLM(LLM):
    def __init__(self):
        super().__init__(
            model="togethercomputer/mixtral-8x7b-instruct",
            api_key=TOGETHER_API_KEY,
            provider="together_ai",  # Specify the provider
            temperature=0.7,
            max_tokens=2000
        ) 