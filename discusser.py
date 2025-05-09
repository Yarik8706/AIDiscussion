from google import genai

class Disscuser:
    def __init__(self, api_key: str, context: str, name: str, model: str = 'gemini-2.0-flash-001'):
        self.api_key = api_key
        self.context = context
        self.name = name
        self.model = model
        self.client = genai.Client(api_key=api_key)

    async def ask(self, discussion_history: list) -> str:
        try:
            # Формируем prompt с историей обсуждения
            history_text = "\n".join(discussion_history)
            prompt = f"{self.context}\n\nТекущий ход обсуждения:\n{history_text}\n\n{self.name}, предположи, что ты скажешь следующее:"
            # 1. Четкий ответ
            response1 = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            answer1 = response1.text.strip() if hasattr(response1, 'text') else str(response1)
            # 2. Переписать как человек
            prompt2 = f"Сделай этот текст похожим на ответ обычного человека: '{answer1}'/ С учетом своего характера: '{self.context}'"
            response2 = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt2
            )
            # answer2 = response2.text.strip() if hasattr(response2, 'text') else str(response2)
            # # 3. Убрать признаки ИИ
            # prompt3 = f"Убери из этого текста все признаки, что его написал ИИ, и сделай его максимально естественным: '{answer2}'. С учетом своего характера: '{self.context}'"
            # response3 = await self.client.aio.models.generate_content(
            #     model=self.model,
            #     contents=prompt3
            # )
            response = response2
            answer = response.text.strip() if hasattr(response, 'text') else str(response)
            return answer
        except Exception as e:
            return f"Gemini API error: {e}"
        
    async def ask_without_humanization(self, consensus_prompt: str, discussion_history: list) -> str:
        try:
            history_text = "\n".join(discussion_history)
            prompt = f"{self.context}\n\nТекущий ход обсуждения:\n{history_text}\n\n{self.name}, {consensus_prompt}"
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip() if hasattr(response, 'text') else str(response)
        except Exception as e:
            return f"Gemini API error: {e}"
