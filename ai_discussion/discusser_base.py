import abc
import asyncio
import re
from typing import List, Optional, Union

from .ai_backends import AIBackend
from .utils import format_history

class BaseDiscusser(abc.ABC):
    """Abstract base class for discussers that participate in AI discussions.
    
    This class defines the common interface and functionality for all discussers,
    regardless of their specific implementation or AI backend used.
    """
    
    def __init__(self, name: str):
        """Initialize the base discusser.
        
        Args:
            name: The name of the discusser
        """
        self.name = name
    
    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the discusser and its resources."""
        pass
    
    @abc.abstractmethod
    async def ask(self, prompt: Union[str, List[str]]) -> str:
        """Ask a question to this discusser with humanization.
        
        Args:
            prompt: The prompt or discussion history to process
            
        Returns:
            The humanized response
        """
        pass
    
    @abc.abstractmethod
    async def ask_without_humanization(self, prompt: str, discussion_history: Optional[List[str]] = None) -> str:
        """Ask a question directly without additional prompt engineering.
        
        Args:
            prompt: The prompt to send to the model
            discussion_history: Optional list of previous messages in the discussion
            
        Returns:
            The raw response
        """
        pass
    
    @abc.abstractmethod
    async def close(self) -> None:
        """Close the discusser and release its resources."""
        pass
    
    def _format_discussion_history(self, prompt: Union[str, List[str]]) -> str:
        """Format the discussion history for processing.
        
        Args:
            prompt: String prompt or list of discussion history entries
            
        Returns:
            Formatted discussion text
        """
        return format_history(prompt)