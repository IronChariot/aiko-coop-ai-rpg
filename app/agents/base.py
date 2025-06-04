from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
from pathlib import Path

# Choose between 'GROK' and 'DEEPSEEK'
MODEL_PROVIDER = 'GROK'

class BaseAgent:
    def __init__(
        self,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        reasoning_effort: str = "high"
    ):
        if MODEL_PROVIDER == 'GROK':
            self.client = OpenAI(
                api_key=os.getenv("GROK_API_KEY"),
                base_url="https://api.x.ai/v1",
            )
            default_model = "grok-3-mini"
        elif MODEL_PROVIDER == 'DEEPSEEK':
            self.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com/v1",
            )
            default_model = "deepseek-reasoner"
        else:
            raise ValueError(f"Unsupported model provider: {MODEL_PROVIDER}")

        self.model = model if model is not None else default_model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort
        self.messages: List[Dict[str, str]] = []
        
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})

    def get_messages(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.messages

    def get_completion(self, user_message: str) -> str:
        """Get a completion from the model."""
        self.add_message("user", user_message)
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
            reasoning_effort=self.reasoning_effort,
        )
        
        response = completion.choices[0].message.content
        self.add_message("assistant", response)
        return response

    def save_memory(self, filepath: Path) -> None:
        """Save the conversation history to a file."""
        filepath.write_text(str(self.messages))

    def load_memory(self, filepath: Path) -> None:
        """Load the conversation history from a file."""
        if filepath.exists():
            self.messages = eval(filepath.read_text()) 