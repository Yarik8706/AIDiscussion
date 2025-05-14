#!/usr/bin/env python3
import os
import asyncio
import json
import logging
from pathlib import Path

# Add parent directory to path to import modules
import sys
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from ai_discussion.discusser_base import BaseDiscusser
from ai_discussion.discusser_factory import DiscusserFactory
from ai_discussion.discusser import Discusser
from ai_discussion.simple_discusser import SimpleDiscusser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_discussion(discussers, question, max_rounds=3):
    """Run a simple discussion between discussers."""
    logger.info(f"Starting discussion on: {question}")
    
    # Create initial discussion history
    discussion_history = [f"Вопрос пользователя: {question}"]
    
    # Run rounds of discussion
    for round_num in range(max_rounds):
        logger.info(f"Round {round_num+1}/{max_rounds}")
        
        for discusser in discussers:
            # Get response from discusser
            response = await discusser.ask(discussion_history)
            
            # Add response to discussion history
            message = f"{discusser.name}: {response}"
            discussion_history.append(message)
            
            # Print the message
            print(f"\n> {message}")
    
    logger.info("Discussion completed")
    return discussion_history

async def create_example_discussers():
    """Create example discussers using different approaches."""
    discussers = []
    
    # Example 1: Create a simple discusser directly
    simple_discusser = SimpleDiscusser(
        name="Логик",
        personality="аналитический",
        responses=[
            "Давайте проанализируем этот вопрос.",
            "Интересно рассмотреть разные точки зрения.",
            "Я считаю, что объективно лучшее решение - это...",
        ]
    )
    await simple_discusser.initialize()
    discussers.append(simple_discusser)
    
    # Example 2: Create an AI discusser directly if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            ai_discusser = Discusser(
                api_key=api_key,
                context="Ты творческий и оригинальный мыслитель.",
                name="Творец",
                model="gpt-3.5-turbo",
                backend_type="openai"
            )
            await ai_discusser.initialize()
            discussers.append(ai_discusser)
        except Exception as e:
            logger.error(f"Failed to create AI discusser: {e}")
    
    # Example 3: Create discussers from a config file
    settings_path = Path(__file__).resolve().parent / "example_settings.json"
    
    # Create example settings file if it doesn't exist
    if not settings_path.exists():
        example_settings = {
            "settings": [
                {
                    "name": "Оптимист",
                    "discusser_type": "simple",
                    "personality": "позитивный",
                    "responses": [
                        "Я уверен, что всё получится!",
                        "Давайте искать возможности, а не проблемы!",
                        "В каждой ситуации есть положительные стороны."
                    ]
                }
            ]
        }
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(example_settings, f, ensure_ascii=False, indent=2)
    
    # Load settings
    with open(settings_path, "r", encoding="utf-8") as f:
        settings_data = json.load(f)
    
    # Create discussers using factory
    factory_discussers = await DiscusserFactory.create_discussers_from_settings(settings_data)
    discussers.extend(factory_discussers)
    
    logger.info(f"Created {len(discussers)} discussers for the example")
    return discussers

async def main():
    """Run the example."""
    print("Creating discussers...")
    discussers = await create_example_discussers()
    
    print("\nStarting discussion...\n")
    question = "Как найти баланс между работой и личной жизнью?"
    await run_discussion(discussers, question)
    
    # Clean up resources
    for discusser in discussers:
        await discusser.close()

if __name__ == "__main__":
    asyncio.run(main()) 