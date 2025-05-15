import abc
from typing import List, Optional, Union
import re
import asyncio

class AIBackend(abc.ABC):
    """Abstract base class for AI backends."""
    
    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the AI backend."""
        pass
    
    @abc.abstractmethod
    async def generate_response(self, prompt: str, discussion_history: Optional[List[str]] = None) -> str:
        """Generate a response from the AI backend.
        
        Args:
            prompt: The prompt to send to the model
            discussion_history: Optional list of previous messages in the discussion
            
        Returns:
            The generated response as a string
        """
        pass
    
    @abc.abstractmethod
    async def close(self) -> None:
        """Close the AI backend and release resources."""
        pass


class GeminiBackend(AIBackend):
    """Gemini-specific implementation of the AI backend."""
    
    def __init__(self, api_key: str, agent_name: str, context: str, model: str = 'gemini-2.0-flash-001'):
        """Initialize the Gemini backend.
        
        Args:
            api_key: The Gemini API key
            agent_name: The name of the agent to use for responses
            context: The system context/instructions for the agent
            model: The model name to use
        """
        self.api_key = api_key
        self.agent_name = agent_name
        self.context = context
        self.model = model
        self.genai_client = None
        self.model_client = None
        
    async def initialize(self) -> None:
        """Initialize the Gemini backend with Google's generative AI API."""
        try:
            import google.generativeai as genai
            
            # Configure the API
            genai.configure(api_key=self.api_key)
            
            # Generate content using the model
            self.genai_client = genai
            self.model_client = genai.GenerativeModel(self.model)
            
            # Ensure the system context is initialized
            self._initialization_test = await self.generate_response("Initialization test")
            
        except ImportError:
            raise ImportError("Google generative AI package is required. Install it with 'pip install google-generativeai'.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini backend: {str(e)}")
    
    async def generate_response(self, prompt: str, discussion_history: Optional[List[str]] = None) -> str:
        """Generate a response using the Gemini model.
        
        Args:
            prompt: The prompt to send to the model
            discussion_history: Optional list of previous messages in the discussion
            
        Returns:
            The generated response as a string
        """
        try:
            # If we have discussion_history, incorporate it into the prompt
            if discussion_history:
                history_text = "\n".join(discussion_history)
                full_prompt = f"Текущий ход обсуждения:\n{history_text}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            # Prepare the message with system context
            system_message = f"{self.context}\n\nИнструкция: {full_prompt}"
            
            # Generate response
            response = await self.model_client.generate_content_async(system_message)
            
            if hasattr(response, 'text'):
                return response.text
            
            # Fallback
            return str(response)
        except Exception as e:
            print(f"Error in generate_response: {e}")
            return f"Error: {str(e)}"
    
    async def close(self) -> None:
        """Close the model client."""
        # No explicit close method for Google's generative AI client
        pass


class OpenAIBackend(AIBackend):
    """OpenAI API implementation of the AI backend."""
    
    def __init__(self, api_key: str, context: str, model: str = 'gpt-4'):
        """Initialize the OpenAI backend.
        
        Args:
            api_key: The OpenAI API key
            context: The system context/instructions
            model: The model name to use (default: gpt-4)
        """
        self.api_key = api_key
        self.context = context
        self.model = model
        self.client = None
        
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            from openai import AsyncOpenAI
            
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("OpenAI package is required for OpenAIBackend. Install it with 'pip install openai'.")
            
    async def generate_response(self, prompt: str, discussion_history: Optional[List[str]] = None) -> str:
        """Generate a response using the OpenAI model.
        
        Args:
            prompt: The prompt to send to the model
            discussion_history: Optional list of previous messages in the discussion
            
        Returns:
            The generated response as a string
        """
        try:
            # Prepare messages
            messages = [{"role": "system", "content": self.context}]
            
            # Add discussion history if provided
            if discussion_history:
                # Convert discussion history to chat format
                for msg in discussion_history:
                    # Extract name and content if in format "Name: Content"
                    if ":" in msg:
                        parts = msg.split(":", 1)
                        name = parts[0].strip()
                        content = parts[1].strip()
                        
                        # Determine role (system vs user)
                        if name.lower() in ["система", "system"]:
                            role = "system"
                        else:
                            role = "user"
                            
                        messages.append({"role": role, "content": content})
                    else:
                        # If no name/role specified, assume user
                        messages.append({"role": "user", "content": msg})
            
            # Add the current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Call the API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in OpenAI generate_response: {e}")
            return f"Error: {str(e)}"
    
    async def close(self) -> None:
        """Close the OpenAI client (no-op for OpenAI client)."""
        pass 