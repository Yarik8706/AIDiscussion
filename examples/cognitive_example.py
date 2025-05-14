#!/usr/bin/env python3
import os
import asyncio
import logging
from pathlib import Path
import sys

# Add parent directory to path to import modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from ai_discussion.cognitive_discusser import CognitiveDiscusser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_cognitive_example():
    """Run an example with the CognitiveDiscusser."""
    logger.info("Initializing cognitive discusser...")
    
    # Get API key from environment variable
    api_key = os.getenv("GENAI_API_KEY_1")
    if not api_key:
        print("Error: Environment variable GENAI_API_KEY_1 not set.")
        print("Please set your Gemini API key and try again.")
        return
    
    # Character context
    context = """
Ты философ, который любит размышлять о сложных вопросах. У тебя аналитический склад ума,
и ты стремишься докопаться до сути проблемы. Ты склонен к глубоким рассуждениям и 
используешь примеры из истории и классической философии. Ты спокоен и рассудителен, 
предпочитаешь взвешенные аргументы эмоциональным высказываниям.
"""
    
    # Create cognitive discusser
    discusser = CognitiveDiscusser(
        api_key=api_key,
        context=context,
        name="Сократ",
        model="gemini-2.0-flash-001",
        backend_type="gemini"
    )
    
    # Initialize the discusser
    await discusser.initialize()
    
    try:
        print("\n===== Когнитивный дискуссер =====\n")
        
        # Example questions to test
        questions = [
            "Что такое счастье?",
            "Как найти свое предназначение в жизни?",
            "Что важнее: свобода или безопасность?"
        ]
        
        # Ask questions using both methods for comparison
        for question in questions:
            print(f"\n\nВопрос: {question}\n")
            
            # Ask with cognitive simulation
            print("=== С когнитивной симуляцией ===")
            start_time = asyncio.get_event_loop().time()
            cognitive_response = await discusser.ask(question)
            end_time = asyncio.get_event_loop().time()
            print(f"Ответ ({end_time - start_time:.2f}s): {cognitive_response}\n")
            
            # Ask without cognitive simulation
            print("=== Без когнитивной симуляции ===")
            start_time = asyncio.get_event_loop().time()
            direct_response = await discusser.ask_without_humanization(question)
            end_time = asyncio.get_event_loop().time()
            print(f"Ответ ({end_time - start_time:.2f}s): {direct_response}\n")
            
            print("-" * 50)
    
    finally:
        # Close the discusser
        await discusser.close()
        logger.info("Discusser closed.")

if __name__ == "__main__":
    asyncio.run(run_cognitive_example()) 