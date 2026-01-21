"""
Ollama Client - Interface to Phi-3 Mini LLM
"""

import ollama
from typing import Optional, Generator
import logging
import hashlib
from functools import lru_cache
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Cache for LLM responses (5 min TTL, max 100 entries)
_response_cache = TTLCache(maxsize=100, ttl=300)


class OllamaClient:
    """Client for interacting with Ollama LLM"""
    
    def __init__(self, model: str = 'phi3:mini', base_url: str = 'http://localhost:11434'):
        """
        Initialize Ollama client
        
        Args:
            model: Model name (default: phi3:mini)
            base_url: Ollama server URL
        """
        self.model = model
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)
        
        # Verify model is available
        self._verify_model()
    
    def _verify_model(self):
        """Check if the model is available"""
        try:
            response = self.client.list()
            logger.info(f"Ollama raw response: {response}")
            
            # Access 'models' field whether it's an object or dict
            if hasattr(response, 'models'):
                models_list = response.models
            elif isinstance(response, dict) and 'models' in response:
                models_list = response['models']
            else:
                logger.warning("Could not find 'models' in Ollama response")
                models_list = []
                
            available_models = []
            for m in models_list:
                # content uses 'model' field, not 'name' based on logs
                # Model(model='phi3:mini', ...)
                if hasattr(m, 'model'):
                    name = m.model
                elif isinstance(m, dict):
                    name = m.get('model') or m.get('name')
                else:
                    name = None
                
                if name:
                    available_models.append(name)

            if self.model not in available_models:
                logger.warning(f"Model {self.model} not found. Available models: {available_models}")
                logger.info(f"To download: ollama pull {self.model}")
        except Exception as e:
            logger.error(f"Could not connect to Ollama server: {e}")
            logger.info("Make sure Ollama is running and accessible")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> str | Generator:
        """
        Generate response from LLM
        
        Args:
            prompt: User prompt
            system_prompt: System prompt to set context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
        
        Returns:
            Generated text or generator for streaming
        """
        messages = []
        
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
        
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                stream=stream,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                }
            )
            
            if stream:
                return self._stream_response(response)
            else:
                return response['message']['content']
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: Could not generate response. {str(e)}"
    
    def _stream_response(self, response) -> Generator:
        """Stream response tokens"""
        for chunk in response:
            if 'message' in chunk:
                content = chunk['message'].get('content', '')
                if content:
                    yield content
    
    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Multi-turn chat
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated response
        """
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                }
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Error: {str(e)}"
    
    def generate_with_history(
        self,
        prompt: str,
        conversation_history: list[dict] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        max_history_messages: int = 10
    ) -> str | Generator:
        """
        Generate response with conversation history context
        
        Args:
            prompt: Current user message
            conversation_history: List of previous messages [{'role': 'user/assistant', 'content': '...'}]
            system_prompt: System prompt to set context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            max_history_messages: Maximum number of previous messages to include
        
        Returns:
            Generated text or generator for streaming
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
        
        # Add conversation history (limit to last N messages)
        if conversation_history:
            recent_history = conversation_history[-max_history_messages:]
            for msg in recent_history:
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        # Add current user message
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                stream=stream,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                }
            )
            
            if stream:
                return self._stream_response(response)
            else:
                return response['message']['content']
        
        except Exception as e:
            logger.error(f"Error generating with history: {e}")
            return f"Error: Could not generate response. {str(e)}"
    
    def generate_cached(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate response with caching.
        Uses a hash of the prompt as cache key.
        Cache TTL is 5 minutes.
        """
        # Create cache key from prompt + system prompt
        cache_key = hashlib.md5(
            f"{self.model}:{system_prompt or ''}:{prompt}".encode()
        ).hexdigest()
        
        # Check cache
        if cache_key in _response_cache:
            logger.debug(f"Cache HIT for prompt hash {cache_key[:8]}")
            return _response_cache[cache_key]
        
        # Generate and cache
        logger.debug(f"Cache MISS for prompt hash {cache_key[:8]}")
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        _response_cache[cache_key] = response
        return response
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Generator:
        """
        Convenience method for streaming generation.
        Returns a generator yielding tokens.
        """
        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
