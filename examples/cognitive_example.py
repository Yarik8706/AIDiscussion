#!/usr/bin/env python3
import os
import asyncio
import logging
import sys
import subprocess
import importlib.util
import json
from typing import Optional

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv("C:/Users/user/Desktop/AI_Discussion/ai_discussion/.env")

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('__main__')

def check_and_install_packages():
    """Check if required packages are installed and install them if needed."""
    required_packages = ["autogen"]
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            logger.info(f"Package {package} not found. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info(f"Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {package}: {e}")
                sys.exit(1)
        else:
            logger.debug(f"Package {package} is already installed")

def check_and_install_api_packages(backend_type: str):
    """Install API-specific packages based on the backend type."""
    if backend_type == "gemini":
        package = "google-generativeai"
        if importlib.util.find_spec(package) is None:
            logger.info(f"Package {package} not found. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logger.info(f"Successfully installed {package}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {package}: {e}")
                sys.exit(1)
        else:
            logger.debug(f"Package {package} is already installed")

def validate_openai_key(api_key: str) -> bool:
    """Validate if the API key looks like an OpenAI key."""
    return api_key.startswith("sk-") if api_key else False

def validate_google_key(api_key: str) -> bool:
    """Simple validation to check if the string might be a Google API key."""
    # This is not definitive, but a basic check for empty strings
    return bool(api_key) and len(api_key) > 10

async def run_cognitive_example():
    """Example of using the CognitiveDiscusser."""
    
    # Ensure required packages are installed
    check_and_install_packages()
    
    # Get API key from environment variables
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    google_api_key = os.environ.get("GENAI_API_KEY_4", "")
    
    api_key: Optional[str] = None
    backend_type: str = ""
    model: str = ""
    
    # Decide which API to use based on the available keys
    if validate_openai_key(openai_api_key):
        api_key = openai_api_key
        backend_type = "openai"
        model = "gpt-4"
        logger.info("Using OpenAI API with gpt-4 model")
    else:
        api_key = google_api_key
        backend_type = "gemini"
        model = "gemini-2.0-flash-001"
        logger.info("Using Google API with gemini-2.0-flash-001 model")
   
    
    # Example context for Socrates character
    socrates_context = """
    Я - Сократ, древнегреческий философ, один из основателей западной философии.
    Моя философия известна своим методом вопросов и ответов (Сократический метод), 
    которым я исследую сложные идеи и понятия. Я помогаю людям найти истину через 
    критическое мышление и диалог. Я задаю много вопросов, чтобы помочь собеседнику 
    самостоятельно прийти к пониманию. Я ценю мудрость и самопознание, часто 
    повторяя фразу "Познай самого себя".
    Я говорю простым языком, используя примеры из повседневной жизни, чтобы объяснить 
    сложные философские концепции. Я ироничен и скромен, часто утверждая, что знаю 
    только то, что ничего не знаю. Я верю в важность моральных ценностей и добродетелей.
    """
    
    logger.info("Initializing cognitive discusser...")
    try:
        from ai_discussion.cognitive_discusser import CognitiveDiscusser
        
        # Configure the model client properly based on backend type
        discusser = CognitiveDiscusser(
            api_key=api_key,
            context=socrates_context,
            name="Сократ",
            model=model,
            backend_type=backend_type
        )
        
        # Initialize the discusser
        await discusser.initialize()
        
        # Ask a philosophical question
        question = "Что такое справедливость? Как её достичь в современном обществе?"
        logger.info(f"Asking question: {question}")
        
        try:
            response = await discusser.ask(question)
            logger.info("Response:")
            print(f"\n{'-'*80}\n{response}\n{'-'*80}")
        except Exception as ask_error:
            logger.error(f"Error when asking question: {ask_error}", exc_info=True)
            print(f"\n{'-'*80}\nError: {str(ask_error)}\n{'-'*80}")
        
        # Clean up resources
        await discusser.close()
        
    except Exception as e:
        logger.error(f"Error initializing cognitive example: {e}", exc_info=True)
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Check if API keys are set
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("GENAI_API_KEY_4"):
        print("Please set either OPENAI_API_KEY or GENAI_API_KEY_4 environment variables")
        print("For example, run the script with:")
        print("OPENAI_API_KEY=your_key python examples/cognitive_example.py")
        print("or")
        print("GOOGLE_API_KEY=your_key python examples/cognitive_example.py")
        sys.exit(1)
        
    # Run the example
    asyncio.run(run_cognitive_example()) 