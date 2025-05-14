import re
from typing import List, Optional, Union
import random

from .discusser_base import BaseDiscusser

class SimpleDiscusser(BaseDiscusser):
    """A simple rule-based discusser implementation.
    
    This class implements a basic discusser that uses predefined
    responses rather than AI models, useful for testing or fallback.
    """
    
    def __init__(self, name: str, personality: str = "friendly", responses: Optional[List[str]] = None):
        """Initialize the simple discusser.
        
        Args:
            name: The name of the discusser
            personality: A descriptor of the discusser's personality
            responses: Optional list of predefined responses
        """
        super().__init__(name)
        self.personality = personality
        self.responses = responses or [
            "Я согласен с предыдущим высказыванием.",
            "Интересная точка зрения, но я думаю немного иначе.",
            "Мне кажется, нам стоит рассмотреть это с другой стороны.",
            "Возможно, мы могли бы найти компромисс?",
            "Я считаю, что это хорошая идея.",
            "Я не уверен, что это лучший подход.",
            "Давайте подумаем о последствиях этого решения.",
        ]
        self.consensus_state = 0  # 0: undecided, 1: leaning yes, 2: leaning no

    async def initialize(self) -> None:
        """Initialize the discusser (no-op for SimpleDiscusser)."""
        # Nothing to initialize for a simple rule-based discusser
        pass
    
    async def ask(self, prompt: Union[str, List[str]]) -> str:
        """Generate a response based on the prompt with personality traits."""
        # Check if we're being asked for consensus
        if isinstance(prompt, str) and "консенсус" in prompt.lower():
            return self._handle_consensus_question()
        
        # Analyze discussion history if provided
        discussion_text = self._format_discussion_history(prompt) if isinstance(prompt, list) else prompt
        
        # Simple rule-based response generation with personality
        if "вопрос пользователя" in discussion_text.lower():
            return f"Как {self.personality} {self.name}, я считаю, что нам нужно внимательно рассмотреть этот вопрос."
        
        # Count messages to vary response strategy
        message_count = len(discussion_text.split('\n')) if isinstance(prompt, list) else 1
        
        # Towards the end, start agreeing more
        if message_count > 10:
            self.consensus_state = 1  # Start leaning towards consensus
            return f"Я думаю, мы приближаемся к решению. {random.choice(self.responses)}"
        
        # Regular response with personality
        personality_prefix = random.choice([
            f"Исходя из моего {self.personality} характера, ",
            f"Как {self.personality} личность, ",
            f"С моей {self.personality} точки зрения, ",
            ""
        ])
        
        return personality_prefix + random.choice(self.responses)
    
    async def ask_without_humanization(self, prompt: str, discussion_history: Optional[List[str]] = None) -> str:
        """Generate a direct response without humanization."""
        # Handle consensus query
        if "диалог закончен" in prompt.lower() or "да или нет" in prompt.lower():
            return self._handle_consensus_question()
            
        # Basic response for other queries
        if discussion_history and len(discussion_history) > 15:
            self.consensus_state = 1  # Start leaning towards consensus if discussion is long
            
        return random.choice(self.responses)
    
    def _handle_consensus_question(self) -> str:
        """Handle consensus queries."""
        # Increase consensus state counter with each query
        self.consensus_state += 1
        
        # After being asked several times, start saying yes
        if self.consensus_state > 2:
            return "ДА"
        else:
            return "НЕТ, нам нужно обсудить еще несколько аспектов."
    
    async def close(self) -> None:
        """Close the discusser (no-op for SimpleDiscusser)."""
        # Nothing to close for a simple rule-based discusser
        pass 