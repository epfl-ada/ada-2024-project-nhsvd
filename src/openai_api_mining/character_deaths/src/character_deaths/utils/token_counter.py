from typing import List, Optional

import tiktoken

from character_deaths.utils.common import SYSTEM_PROMPT, construct_user_prompt

class TokenCounter:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.encoding = tiktoken.encoding_for_model(model)
        self.system_tokens = len(self.encoding.encode(SYSTEM_PROMPT))
        
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def estimate_request_tokens(self, plot_summary: str, character_names: Optional[List[str]]) -> int:
        prompt = construct_user_prompt(plot_summary=plot_summary, character_names=character_names)
        prompt_tokens = self.count_tokens(prompt)
        total_tokens = self.system_tokens + prompt_tokens + 50
        return total_tokens
