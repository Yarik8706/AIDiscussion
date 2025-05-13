import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient
import re
import json

class Discusser:
    def __init__(self, api_key: str, context: str, name: str, model: str = 'gemini-2.0-flash-001'):
        self.api_key = api_key
        self.context = context
        self.name = name
        self.model = model
        
        # Transliterate Russian name to ASCII for AutoGen compatibility
        self.agent_name = self._transliterate_name(name)
        
        # Initialize OpenAI-compatible client for Gemini
        self.model_client = OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
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
            system_message=context  # Set the context as system message
        )

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

    async def ask(self, prompt):
        """Ask a question to this discusser with humanization."""
        # Check if prompt is a string or a list (discussion history)
        if isinstance(prompt, list):
            discussion_text = "\n".join(prompt)
            prompt_with_humanization = f"Текущий ход обсуждения:\n{discussion_text}\n\n{self.name}, предположи, что ты скажешь следующее:"
        else:
            prompt_with_humanization = f"Текущий ход обсуждения:\n{prompt}\n\n{self.name}, предположи, что ты скажешь следующее:"
        
        result = await self.ask_without_humanization(prompt_with_humanization)
        
        # Now add the persona context to get a clean humanized response
        humanize_prompt = f"Сделай этот текст похожим на ответ обычного человека: '{result}' С учетом своего характера: '{self.context}'"
        humanized_result = await self.ask_without_humanization(humanize_prompt)
        return humanized_result

    async def ask_without_humanization(self, prompt, discussion_history=None):
        """Ask a question directly to the model without additional prompt engineering.
        
        Args:
            prompt: The prompt to send to the model
            discussion_history: Optional list of previous messages in the discussion
        """
        try:
            # If we have discussion_history, incorporate it into the prompt
            if discussion_history:
                history_text = "\n".join(discussion_history)
                full_prompt = f"Текущий ход обсуждения:\n{history_text}\n\n{self.name}, {prompt}"
            else:
                full_prompt = prompt
            
            # Pass prompt as a named parameter 'task', not as a positional parameter
            task_result = await self.agent.run(task=full_prompt)
            response = self._extract_response_text(task_result)
            return response
        except Exception as e:
            print(f"Error in ask_without_humanization: {e}")
            return f"Error: {str(e)}"

    async def close(self):
        """Close the model client."""
        if hasattr(self, 'model_client'):
            try:
                await self.model_client.close()
            except:
                pass 