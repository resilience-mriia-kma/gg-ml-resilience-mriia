from typing import Protocol


class ILLMService(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...
