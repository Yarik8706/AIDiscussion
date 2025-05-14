import asyncio
from typing import List, Optional, Union, Dict, Any
import re

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import BaseGroupChat
from autogen_agentchat.teams._group_chat._base_group_chat_manager import BaseGroupChatManager


from .discusser import Discusser

class CognitiveDiscusser(Discusser):
    """A discusser that simulates cognitive processes using a group chat of specialized agents.
    
    This discusser uses autogen's GroupChat to create a more realistic thinking process
    before responding to questions. It simulates different cognitive modules like
    perception, memory, reasoning, emotion, decision making, and language.
    """
    
    def __init__(
        self, 
        api_key: str, 
        context: str, 
        name: str, 
        model: str = 'gemini-2.0-flash-001', 
        backend_type: str = 'gemini',
        cognitive_agents: Optional[Dict[str, str]] = None
    ):
        """Initialize the cognitive discusser.
        
        Args:
            api_key: The API key for the AI service
            context: The system context/instructions for the agent
            name: The name of the discusser
            model: The model name to use
            backend_type: The type of AI backend to use
            cognitive_agents: Optional custom definitions for cognitive agents
        """
        super().__init__(api_key, context, name, model, backend_type)
        
        # Default cognitive agent definitions if none provided
        self.cognitive_agents = cognitive_agents or {
            "Perception": "Ты модуль восприятия. Твоя задача - интерпретировать входные данные и передавать их другим модулям. Анализируй контекст и выдели ключевую информацию из запроса.",
            
            "Memory": f"Ты модуль памяти персонажа {name}. Твоя задача - вспоминать прошлый опыт и знания, связанные с запросом. Опирайся на личность персонажа: {context}",
            
            "Reasoning": "Ты модуль рассуждения. Твоя задача - логически анализировать информацию, строить причинно-следственные связи и формулировать аргументы.",
            
            "Emotion": f"Ты эмоциональный модуль персонажа {name}. Твоя задача - добавлять эмоциональную реакцию, подходящую для личности: {context}. Предложи, какие чувства персонаж испытывает в отношении темы.",
            
            "Decision": f"Ты модуль принятия решений персонажа {name}. Твоя задача - на основе информации от других модулей, сформулировать ключевые мысли для ответа, соответствующие личности: {context}",
            
            "Language": f"Ты языковой модуль персонажа {name}. Твоя задача - преобразовать окончательное решение в естественный текст с речевыми особенностями, соответствующими личности: {context}. Сформулируй окончательный ответ от первого лица."
        }
        
        # Agents will be initialized in the initialize method
        self.agents = {}
        self.group_chat = None
        self.manager = None
        
    async def initialize(self) -> None:
        """Initialize the AI backend and the cognitive agents."""
        # Initialize the main backend for ask_without_humanization
        await super().initialize()
        
        # Initialize cognitive agents for the group chat simulation
        await self._initialize_cognitive_agents()
        
    async def _initialize_cognitive_agents(self) -> None:
        """Initialize the cognitive agents for the group chat."""
        # Create assistant agents for each cognitive module
        for agent_name, system_message in self.cognitive_agents.items():
            agent = AssistantAgent(
                name=agent_name,
                model_client=self.backend.model_client,  # Use the same model client as the main backend
                system_message=system_message
            )
            self.agents[agent_name] = agent
        
        # Create a proxy agent to initiate the chat
        # We'll use this in the ask method to simulate the user input
        self.proxy_agent = AssistantAgent(
            name="Proxy",
            model_client=self.backend.model_client,
            system_message="Ты прокси-агент, который передает запросы от пользователя в когнитивную систему."
        )
        
        # Configure the group chat with all agents
        agent_list = list(self.agents.values()) + [self.proxy_agent]
        self.group_chat = BaseGroupChat(
            agents=agent_list,
            messages=[],
            max_round=len(self.agents)  # Limit discussion rounds to the number of agents
        )
        
        # Create the group chat manager
        self.manager = BaseGroupChatManager(
            groupchat=self.group_chat, 
            model_client=self.backend.model_client
        )
    
    async def ask(self, prompt: Union[str, List[str]]) -> str:
        """Ask a question using cognitive simulation for a more realistic response.
        
        This method uses autogen's GroupChat to simulate different cognitive processes
        before generating a response, creating a more human-like thinking process.
        
        Args:
            prompt: The prompt or discussion history to process
            
        Returns:
            The humanized response after cognitive simulation
        """
        # Format the prompt if it's a list of discussion history
        discussion_text = self._format_discussion_history(prompt) if isinstance(prompt, list) else prompt
        
        # Create the task for cognitive processing
        cognitive_prompt = f"""
Тебе нужно сгенерировать реалистичный ответ для персонажа {self.name} с учетом его личности: 
{self.context}

Текущий ход обсуждения:
{discussion_text}

Представь, что ты этот персонаж. Как бы ты ответил на этот запрос?
"""
        
        try:
            # Reset the chat for a new conversation
            self.group_chat.messages = []
            
            # Run the cognitive simulation using the group chat
            result = await self.proxy_agent.run(task=cognitive_prompt, manager=self.manager)
            
            # Extract the final response from the group chat
            # The last message from the Language agent is typically the final response
            response = self._extract_final_response(result)
            
            return response
        except Exception as e:
            print(f"Error in cognitive simulation: {e}")
            
            # Fallback to regular ask_without_humanization if the cognitive simulation fails
            return await super().ask(prompt)
    
    def _extract_final_response(self, result):
        """Extract the final response from the group chat result."""
        try:
            # If the result is already a string, return it
            if isinstance(result, str):
                return result
            
            # Check if the result has messages attribute
            if hasattr(result, 'messages') and result.messages:
                # Try to find the last message from the Language agent
                for message in reversed(result.messages):
                    if hasattr(message, 'source') and message.source == "Language":
                        if hasattr(message, 'content'):
                            # Extract just the response part, removing any agent discussion
                            response = message.content
                            # Remove any prefixes like "Language:" or role indicators
                            response = re.sub(r'^.*?:', '', response, flags=re.MULTILINE).strip()
                            return response
                
                # If no Language agent message found, use the last message
                last_message = result.messages[-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content
                    response = re.sub(r'^.*?:', '', response, flags=re.MULTILINE).strip()
                    return response
            
            # Convert to string and do basic cleaning if we couldn't extract a clean response
            return str(result)
        except Exception as e:
            print(f"Error extracting final response: {e}")
            return str(result)
    
    async def close(self) -> None:
        """Close all resources."""
        # Close the main backend
        await super().close()
        
        # No need to close agents as they share the same model client with the backend 