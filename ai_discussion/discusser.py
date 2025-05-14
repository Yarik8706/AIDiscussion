import asyncio
import re
from typing import Optional, List, Union

from .ai_backends import AIBackend, GeminiBackend, OpenAIBackend
from .discusser_base import BaseDiscusser

class Discusser(BaseDiscusser):
    """AI discusser implementation using pluggable AI backends.
    
    This class implements a discusser that can use different AI backends
    to generate responses in a discussion.
    """
    
    def __init__(self, api_key: str, context: str, name: str, model: str = 'gemini-2.0-flash-001', backend_type: str = 'gemini'):
        """Initialize the discusser.
        
        Args:
            api_key: The API key for the AI service
            context: The system context/instructions for the agent
            name: The name of the discusser
            model: The model name to use
            backend_type: The type of AI backend to use
        """
        super().__init__(name)
        self.api_key = api_key
        self.context = context
        self.model = model
        
        # Transliterate Russian name to ASCII for AutoGen compatibility
        self.agent_name = self._transliterate_name(name)
        
        # Initialize AI backend based on the specified type
        self.backend = self._create_backend(backend_type)
        
    async def initialize(self) -> None:
        """Initialize the AI backend."""
        await self.backend.initialize()
        
    def _create_backend(self, backend_type: str) -> AIBackend:
        """Create the appropriate AI backend based on the specified type."""
        if backend_type.lower() == 'gemini':
            return GeminiBackend(
                api_key=self.api_key,
                agent_name=self.agent_name,
                context=self.context,
                model=self.model
            )
        elif backend_type.lower() == 'openai':
            # For OpenAI, we use a different default model if none is specified
            model = self.model if 'gpt' in self.model.lower() else 'gpt-4'
            return OpenAIBackend(
                api_key=self.api_key,
                context=self.context,
                model=model
            )
        else:
            raise ValueError(f"Unsupported backend type: {backend_type}")

    def _transliterate_name(self, name):
        """Transliterate Russian name to ASCII for compatibility with AutoGen requirements."""
        transliteration_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
            'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
            'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
            'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
            'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '',
            'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
        }
        
        # Replace spaces with underscores and transliterate characters
        result = ""
        for char in name:
            if char in transliteration_map:
                result += transliteration_map[char]
            elif char.isalnum() or char == '_':
                result += char
            else:
                result += '_'
        
        # Ensure the name is valid by starting with a letter and containing only letters, numbers, and underscores
        if not result or not result[0].isalpha():
            result = 'agent_' + result
            
        return result

    async def ask(self, prompt: Union[str, List[str]]) -> str:
        """Ask a question to this discusser with humanization."""
        # Check if prompt is a string or a list (discussion history)
        if isinstance(prompt, list):
            discussion_text = self._format_discussion_history(prompt)
            prompt_with_humanization = f"Текущий ход обсуждения:\n{discussion_text}\n\n{self.name}, предположи, что ты скажешь следующее:"
        else:
            prompt_with_humanization = f"Текущий ход обсуждения:\n{prompt}\n\n{self.name}, предположи, что ты скажешь следующее:"
        
        result = await self.ask_without_humanization(prompt_with_humanization)
        
        # Now add the persona context to get a clean humanized response
        humanize_prompt = f"Сделай этот текст похожим на ответ обычного человека: '{result}' С учетом своего характера: '{self.context}'"
        humanized_result = await self.ask_without_humanization(humanize_prompt)
        return humanized_result

    async def ask_without_humanization(self, prompt: str, discussion_history: Optional[List[str]] = None) -> str:
        """Ask a question directly to the model without additional prompt engineering."""
        try:
            return await self.backend.generate_response(prompt, discussion_history)
        except Exception as e:
            print(f"Error in ask_without_humanization: {e}")
            return f"Error: {str(e)}"

    async def close(self) -> None:
        """Close the model client."""
        await self.backend.close() 