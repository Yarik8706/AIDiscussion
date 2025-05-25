import asyncio
import logging

from dotenv import load_dotenv

from ai_discussion.cognitive_discusser import CognitiveDiscusser

load_dotenv("C:/Users/user/Desktop/AI_Discussion/ai_discussion/.env")

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('__main__')

def validate_openai_key(api_key: str) -> bool:
    """Validate if the API key looks like an OpenAI key."""
    return api_key.startswith("sk-") if api_key else False

def validate_google_key(api_key: str) -> bool:
    """Simple validation to check if the string might be a Google API key."""
    # This is not definitive, but a basic check for empty strings
    return bool(api_key) and len(api_key) > 10

async def run_cognitive_example():
    """Example of using the CognitiveDiscusser."""
    google_api_key = "AIzaSyCEJn71H8w6388znhxjtWZLdJyCHOfYVc8"
    
    api_key = google_api_key
    backend_type = "gemini"
    model = "gemini-2.0-flash"
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
        question = "User: Что такое справедливость? Как её достичь в современном обществе?"
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
    asyncio.run(run_cognitive_example()) 