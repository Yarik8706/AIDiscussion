
from typing import List, Optional, Union, Dict
import re
import logging

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat

from autogen_ext.models.openai import OpenAIChatCompletionClient

from ai_discussion.discusser import Discusser

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CognitiveDiscusser')

class CognitiveDiscusser(Discusser):
    """A discusser that simulates cognitive processes using a group chat of specialized agents.
    This discusser uses autogen's SelectorGroupChat to create a more realistic thinking process
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
            "Context": f"Ты модуль Context для {name}. Получаешь ход диалога и личность: {context}. Выделяй ключевую информацию в виде списка ключевых фактов.",
            "Reasoning": f"Ты модуль Reasoning для {name}. На входе — данные от Context. Выводи причинно-следственные связи и аргументы в виде списка.",
            "Emotion": f"Ты модуль Emotion для {name}. На входе — данные от Context. Определи тон и эмоции персонажа в виде списка меток.",
            "Decision": f"Ты модуль Decision для {name}. На входе — Reasoning и Emotion. Сформируй ключевые тезисы ответа в виде списка.",
            "Coordinator": f"Ты модуль Coordinator для {name}. На входе — Context, Reasoning, Emotion, Decision. Собери единый ответ, включающий: приветствие, обзор проблемы, аргументы, примеры, уточняющие вопросы. Выводи только итоговый текст.",
        }
        logger.debug(f"Configured {len(self.cognitive_agents)} cognitive agents")

        # Agents will be initialized in the initialize method
        self.agents = {}
        self.group_chat = None

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
            model_client = OpenAIChatCompletionClient(
                model=self.model,
                api_key=self.api_key
            )
            # Create assistant agents for each cognitive module
            for agent_name, system_message in self.cognitive_agents.items():
                logger.debug(f"Creating agent: {agent_name}")
                try:

                    agent = AssistantAgent(
                        name=agent_name,
                        model_client=model_client,
                        system_message=system_message
                    )
                    self.agents[agent_name] = agent
                    logger.debug(f"Agent '{agent_name}' created successfully")
                except Exception as e:
                    logger.error(f"Failed to create agent '{agent_name}': {e}", exc_info=True)
                    raise

            # Configure the group chat with all agents
            logger.debug("Creating group chat with all agents")
            try:
                agent_list = list(self.agents.values())
                self.group_chat = RoundRobinGroupChat(
                    agent_list,
                    max_turns=len(agent_list)
                )
                logger.debug(f"Group chat created with {len(agent_list)} agents")
            except Exception as e:
                logger.error(f"Failed to create group chat: {e}", exc_info=True)
                raise

            logger.info("Cognitive agents initialization completed successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cognitive agents: {e}", exc_info=True)
            raise

    async def ask(self, prompt: Union[str, List[str]]) -> str:
        """Ask a question using cognitive simulation for a more realistic response.
        This method uses autogen's SelectorGroupChat to simulate different cognitive processes
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
Текущий ход обсуждения:
{discussion_text}
Конец хода обсуждения.
Модули персонажа {self.name}:
"""
        logger.debug(f"Created cognitive prompt, length: {len(cognitive_prompt)} characters")

        try:
            # Reset the chat for a new conversation
            logger.debug("Resetting group chat messages")
            self.group_chat.messages = []

            # Run the cognitive simulation using the group chat
            logger.info("Starting cognitive simulation with group chat")

            if self.group_chat is None:
                logger.error("Group chat is None - initialization may have failed")
                raise ValueError("Group chat not initialized")

            logger.debug("Calling proxy_agent.initiate_chat with task")
            result = await self.group_chat.run(task=cognitive_prompt)
            logger.debug(f"Cognitive simulation completed")
            return "\n ----------------------- \n".join(i.content for i in result.messages)

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