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
        self.agent = None
        self.model_client = None
        
    async def initialize(self) -> None:
        """Initialize the Gemini backend with AutoGen."""
        from autogen_agentchat.agents import AssistantAgent
        from autogen_core.models import ModelInfo
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        # Initialize OpenAI-compatible client for Gemini
        self.model_client = OpenAIChatCompletionClient(
            model=self.model,
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            model_info=ModelInfo(
                vision=False,  # Adjust based on model capabilities
                max_tokens=4096,
                max_input_tokens=8192,
                max_output_tokens=2048,
                function_calling=True,    # Required field
                json_output=True,         # Required field
                family="google",          # Specify the model family
                structured_output=True    # Required field
            ),
        )
        
        # Create agent with the correct parameter (model_client, not llm)
        self.agent = AssistantAgent(
            name=self.agent_name,
            model_client=self.model_client,
            system_message=self.context  # Set the context as system message
        )
    
    def _extract_response_text(self, task_result):
        """Extract clean text from the TaskResult object."""
        try:
            # If it's already a string, return it
            if isinstance(task_result, str):
                return task_result
            
            # Handle TaskResult objects based on AutoGen documentation
            # TaskResult contains messages and stopreason
            if hasattr(task_result, 'messages') and task_result.messages:
                # Get the last message from the agent
                for message in reversed(task_result.messages):
                    # Look for the agent's message (usually the last one from our agent)
                    if hasattr(message, 'source') and message.source == self.agent_name:
                        if hasattr(message, 'content'):
                            return message.content
            
            # If we couldn't extract using the structured approach, try converting to string
            text = str(task_result)
            
            # Clean up the response by removing metadata and technical details
            text = re.sub(r'messages=\[.*?\]', '', text, flags=re.DOTALL)
            text = re.sub(r'TextMessage\(.*?\)', '', text, flags=re.DOTALL)
            text = re.sub(r'source=\'.*?\'', '', text)
            text = re.sub(r'modelsusage=.*?,', '', text)
            text = re.sub(r'metadata=\{\},', '', text)
            text = re.sub(r'type=\'TextMessage\'', '', text)
            text = re.sub(r'stopreason=.*', '', text)
            text = re.sub(r'content=\'(.*?)\'', r'\1', text)
            text = re.sub(r'[\[\],()]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
        except Exception as e:
            print(f"Error extracting response: {e}")
            return str(task_result)
    
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
            
            # Pass prompt as a named parameter 'task', not as a positional parameter
            task_result = await self.agent.run(task=full_prompt)
            response = self._extract_response_text(task_result)
            return response
        except Exception as e:
            print(f"Error in generate_response: {e}")
            return f"Error: {str(e)}"
    
    async def close(self) -> None:
        """Close the model client."""
        if hasattr(self, 'model_client'):
            try:
                await self.model_client.close()
            except:
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