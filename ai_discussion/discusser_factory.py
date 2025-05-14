import os
from typing import Dict, List, Optional, Union, Any

from .discusser_base import BaseDiscusser
from .discusser import Discusser
from .simple_discusser import SimpleDiscusser
from .cognitive_discusser import CognitiveDiscusser

class DiscusserFactory:
    """Factory class for creating different types of discussers."""
    
    @staticmethod
    async def create_discusser(
        discusser_type: str,
        name: str,
        config: Dict[str, Any]
    ) -> BaseDiscusser:
        """Create a discusser of the specified type.
        
        Args:
            discusser_type: The type of discusser to create ('ai', 'simple', 'cognitive', etc.)
            name: The name of the discusser
            config: Configuration dictionary for the discusser
            
        Returns:
            An initialized discusser instance
            
        Raises:
            ValueError: If the discusser type is not supported
        """
        discusser = None
        
        if discusser_type.lower() == 'ai':
            # Create an AI-powered discusser
            api_key = config.get('api_key') or os.getenv(config.get('env_token_name', ''))
            if not api_key:
                raise ValueError(f"API key not found for {name}")
            
            context = config.get('context', '')
            # Load context from file if specified
            if 'character_path' in config and not context:
                try:
                    with open(config['character_path'], 'r', encoding='utf-8') as f:
                        context = f.read().strip()
                except Exception as e:
                    raise ValueError(f"Error reading character file: {e}")
            
            # Add general context if specified
            if 'general_context' in config:
                context = f"{context}\n{config['general_context']}"
                
            # Create the Discusser instance
            discusser = Discusser(
                api_key=api_key,
                context=context,
                name=name,
                model=config.get('model', 'gemini-2.0-flash-001'),
                backend_type=config.get('backend_type', 'gemini')
            )
        
        elif discusser_type.lower() == 'cognitive':
            # Create a cognitive discusser that uses group chat for thinking
            api_key = config.get('api_key') or os.getenv(config.get('env_token_name', ''))
            if not api_key:
                raise ValueError(f"API key not found for {name}")
            
            context = config.get('context', '')
            # Load context from file if specified
            if 'character_path' in config and not context:
                try:
                    with open(config['character_path'], 'r', encoding='utf-8') as f:
                        context = f.read().strip()
                except Exception as e:
                    raise ValueError(f"Error reading character file: {e}")
            
            # Add general context if specified
            if 'general_context' in config:
                context = f"{context}\n{config['general_context']}"
                
            # Custom cognitive agents if specified
            cognitive_agents = config.get('cognitive_agents', None)
                
            # Create the CognitiveDiscusser instance
            discusser = CognitiveDiscusser(
                api_key=api_key,
                context=context,
                name=name,
                model=config.get('model', 'gemini-2.0-flash-001'),
                backend_type=config.get('backend_type', 'gemini'),
                cognitive_agents=cognitive_agents
            )
        
        elif discusser_type.lower() == 'simple':
            # Create a simple rule-based discusser
            discusser = SimpleDiscusser(
                name=name,
                personality=config.get('personality', 'friendly'),
                responses=config.get('responses', None)
            )
        
        else:
            raise ValueError(f"Unsupported discusser type: {discusser_type}")
        
        # Initialize the discusser
        await discusser.initialize()
        
        return discusser
    
    @staticmethod
    async def create_discussers_from_settings(settings_data: Dict[str, Any]) -> List[BaseDiscusser]:
        """Create multiple discussers from settings data.
        
        Args:
            settings_data: Dictionary containing settings for multiple discussers
            
        Returns:
            List of initialized discussers
        """
        discussers = []
        
        # Load general context if available
        general_context = ''
        if 'general_context_path' in settings_data:
            try:
                with open(settings_data['general_context_path'], 'r', encoding='utf-8') as f:
                    general_context = f.read().strip()
            except Exception as e:
                print(f"Warning: Could not load general context: {e}")
        
        # Create discussers from settings
        for item in settings_data.get('settings', []):
            try:
                # Prepare config
                config = dict(item)
                config['general_context'] = general_context
                
                # Determine discusser type
                discusser_type = item.get('discusser_type', 'ai')
                
                # Create and initialize the discusser
                discusser = await DiscusserFactory.create_discusser(
                    discusser_type=discusser_type,
                    name=item.get('name', f"Discusser_{len(discussers)}"),
                    config=config
                )
                
                discussers.append(discusser)
                print(f"Created {discusser_type} discusser: {item.get('name')}")
            except Exception as e:
                print(f"Error creating discusser: {e}")
        
        return discussers 