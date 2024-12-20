from typing import List, Optional
from pathlib import Path

import tiktoken

from api_mining.models.core import DataType
from api_mining.utils.common import read_system_prompt, construct_user_prompt

class TokenCounter:
    """Utility class for estimating token counts for OpenAI API requests"""
    def __init__(self, data_type: DataType, model: str = "gpt-4o-mini"):
        self.encoding = tiktoken.encoding_for_model(model)
        self.system_tokens = len(self.encoding.encode(read_system_prompt(data_type)))
        
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def estimate_request_tokens(self, plot_summary: str, character_names: Optional[List[str]]) -> int:
        prompt = construct_user_prompt(plot_summary=plot_summary, character_names=character_names)
        prompt_tokens = self.count_tokens(prompt)
        total_tokens = self.system_tokens + prompt_tokens + 50
        return total_tokens
