import asyncio
from typing import List, Optional, Union, Dict, Any
import re
import logging

import autogen
from autogen import AssistantAgent, GroupChat, GroupChatManager

from .discusser import Discusser

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CognitiveDiscusser')

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
        logger.info(f"Initializing CognitiveDiscusser named '{name}' with {backend_type} backend")
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
        logger.debug(f"Configured {len(self.cognitive_agents)} cognitive agents")
        
        # Agents will be initialized in the initialize method
        self.agents = {}
        self.group_chat = None
        self.manager = None
        self.proxy_agent = None
        
    async def initialize(self) -> None:
        """Initialize the AI backend and the cognitive agents."""
        logger.info("Starting initialization of CognitiveDiscusser")
        try:
            # Initialize the main backend for ask_without_humanization
            logger.debug("Initializing the main AI backend")
            await super().initialize()
            logger.debug("Main AI backend initialized successfully")
            
            # Initialize cognitive agents for the group chat simulation
            logger.debug("Starting cognitive agents initialization")
            await self._initialize_cognitive_agents()
            logger.info("CognitiveDiscusser initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize CognitiveDiscusser: {e}", exc_info=True)
            raise
        
    async def _initialize_cognitive_agents(self) -> None:
        """Initialize the cognitive agents for the group chat."""
        logger.debug("Creating assistant agents for each cognitive module")
        try:
            # Create assistant agents for each cognitive module
            for agent_name, system_message in self.cognitive_agents.items():
                logger.debug(f"Creating agent: {agent_name}")
                
                try:
                    agent = AssistantAgent(
                        name=agent_name,
                        llm_config={"config_list": [{"model": self.model, "api_key": self.api_key}]},
                        system_message=system_message
                    )
                    self.agents[agent_name] = agent
                    logger.debug(f"Agent '{agent_name}' created successfully")
                except Exception as e:
                    logger.error(f"Failed to create agent '{agent_name}': {e}", exc_info=True)
                    raise
            
            # Create a proxy agent to initiate the chat
            logger.debug("Creating proxy agent")
            try:
                self.proxy_agent = AssistantAgent(
                    name="Proxy",
                    llm_config={"config_list": [{"model": self.model, "api_key": self.api_key}]},
                    system_message="Ты прокси-агент, который передает запросы от пользователя в когнитивную систему."
                )
                logger.debug("Proxy agent created successfully")
            except Exception as e:
                logger.error(f"Failed to create proxy agent: {e}", exc_info=True)
                raise
            
            # Configure the group chat with all agents
            logger.debug("Creating group chat with all agents")
            try:
                agent_list = list(self.agents.values()) + [self.proxy_agent]
                self.group_chat = GroupChat(
                    agents=agent_list,
                    messages=[],
                    max_round=len(self.agents)  # Limit discussion rounds to the number of agents
                )
                logger.debug(f"Group chat created with {len(agent_list)} agents")
            except Exception as e:
                logger.error(f"Failed to create group chat: {e}", exc_info=True)
                raise
            
            # Create the group chat manager
            logger.debug("Creating group chat manager")
            try:
                self.manager = GroupChatManager(
                    groupchat=self.group_chat,
                    llm_config={"config_list": [{"model": self.model, "api_key": self.api_key}]}
                )
                logger.debug("Group chat manager created successfully")
            except Exception as e:
                logger.error(f"Failed to create group chat manager: {e}", exc_info=True)
                raise
                
            logger.info("Cognitive agents initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cognitive agents: {e}", exc_info=True)
            raise
    
    async def ask(self, prompt: Union[str, List[str]]) -> str:
        """Ask a question using cognitive simulation for a more realistic response.
        
        This method uses autogen's GroupChat to simulate different cognitive processes
        before generating a response, creating a more human-like thinking process.
        
        Args:
            prompt: The prompt or discussion history to process
            
        Returns:
            The humanized response after cognitive simulation
        """
        logger.info("Processing ask request with cognitive simulation")
        
        # Format the prompt if it's a list of discussion history
        logger.debug("Formatting prompt")
        discussion_text = self._format_discussion_history(prompt) if isinstance(prompt, list) else prompt
        logger.debug(f"Prompt formatted, length: {len(discussion_text)} characters")
        
        # Create the task for cognitive processing
        cognitive_prompt = f"""
Тебе нужно сгенерировать реалистичный ответ для персонажа {self.name} с учетом его личности: 
{self.context}

Текущий ход обсуждения:
{discussion_text}

Представь, что ты этот персонаж. Как бы ты ответил на этот запрос?
"""
        logger.debug(f"Created cognitive prompt, length: {len(cognitive_prompt)} characters")
        
        try:
            # Reset the chat for a new conversation
            logger.debug("Resetting group chat messages")
            self.group_chat.messages = []
            
            # Run the cognitive simulation using the group chat
            logger.info("Starting cognitive simulation with group chat")
            if self.proxy_agent is None:
                logger.error("Proxy agent is None - initialization may have failed")
                raise ValueError("Proxy agent not initialized")
                
            if self.manager is None:
                logger.error("Group chat manager is None - initialization may have failed")
                raise ValueError("Group chat manager not initialized")
                
            logger.debug("Calling proxy_agent.initiate_chat with task")
            result = await self.proxy_agent.initiate_chat(
                self.manager,
                message=cognitive_prompt
            )
            logger.debug(f"Cognitive simulation completed")
            
            # Extract the final response from the group chat
            logger.debug("Extracting final response from cognitive simulation result")
            response = self._extract_final_response(self.group_chat.messages)
            logger.info(f"Final response extracted, length: {len(response) if response else 0} characters")
            
            return response
        except Exception as e:
            logger.error(f"Error in cognitive simulation: {e}", exc_info=True)
            logger.info("Falling back to regular ask_without_humanization")
            
            # Fallback to regular ask_without_humanization if the cognitive simulation fails
            try:
                result = await super().ask(prompt)
                logger.info("Fallback response generated successfully")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
                return f"Error in cognitive processing: {e}. Fallback also failed: {fallback_error}"
    
    def _extract_final_response(self, messages):
        """Extract the final response from the group chat messages."""
        logger.debug(f"Extracting final response from {len(messages) if messages else 0} messages")
        try:
            # If no messages, return empty string
            if not messages:
                logger.debug("No messages to extract from")
                return ""
            
            # Try to find the last message from the Language agent
            for message in reversed(messages):
                if 'name' in message and message['name'] == "Language":
                    logger.debug("Found message from Language agent")
                    if 'content' in message:
                        # Extract just the response part, removing any agent discussion
                        response = message['content']
                        logger.debug(f"Raw Language agent content: {response[:100]}...")
                        # Remove any prefixes like "Language:" or role indicators
                        response = re.sub(r'^.*?:', '', response, flags=re.MULTILINE).strip()
                        logger.debug(f"Cleaned Language agent response: {response[:100]}...")
                        return response
            
            logger.debug("No Language agent message found, using last message")
            # If no Language agent message found, use the last message
            last_message = messages[-1]
            if 'content' in last_message:
                response = last_message['content']
                logger.debug(f"Raw last message content: {response[:100]}...")
                response = re.sub(r'^.*?:', '', response, flags=re.MULTILINE).strip()
                logger.debug(f"Cleaned last message response: {response[:100]}...")
                return response
            else:
                logger.debug("No content in last message")
                return str(last_message)
        except Exception as e:
            logger.error(f"Error extracting final response: {e}", exc_info=True)
            return str(messages[-1] if messages else "No response")
    
    async def close(self) -> None:
        """Close all resources."""
        logger.info("Closing CognitiveDiscusser resources")
        try:
            # Close the main backend
            logger.debug("Closing main backend")
            await super().close()
            logger.debug("Main backend closed successfully")
            
            # No need to close agents as they share the same model client with the backend
            logger.info("CognitiveDiscusser resources closed successfully")
        except Exception as e:
            logger.error(f"Error closing CognitiveDiscusser resources: {e}", exc_info=True) 