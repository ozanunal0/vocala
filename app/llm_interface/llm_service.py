"""
Central LLM service for generating vocabulary content.
"""

import asyncio
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Central service for LLM-powered content generation."""
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.timeout = settings.llm_request_timeout
        self.max_retries = settings.llm_max_retries
        
        # Initialize provider clients
        self._openai_client = None
        self._google_client = None
        
        if self.provider == "openai" and settings.openai_api_key:
            self._init_openai()
        elif self.provider == "google" and settings.google_ai_api_key:
            self._init_google()
        elif self.provider != "mock":
            logger.warning(f"LLM provider '{self.provider}' not properly configured, falling back to mock")
            self.provider = "mock"
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            import openai
            self._openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized")
        except ImportError:
            logger.error("OpenAI package not installed")
            self.provider = "mock"
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.provider = "mock"
    
    def _init_google(self):
        """Initialize Google AI client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_ai_api_key)
            self._google_client = genai.GenerativeModel(settings.google_ai_model)
            logger.info("Google AI client initialized")
        except ImportError:
            logger.error("Google Generative AI package not installed")
            self.provider = "mock"
        except Exception as e:
            logger.error(f"Failed to initialize Google AI client: {e}")
            self.provider = "mock"
    
    async def generate_vocabulary_set(
        self,
        user_profile: Dict[str, Any],
        word_count: int,
        difficulty_reference: str = "Oxford3000_B1_B2"
    ) -> List[Dict[str, Any]]:
        """
        Generate a set of vocabulary words with examples.
        
        Args:
            user_profile: User information (difficulty level, learned words, etc.)
            word_count: Number of words to generate
            difficulty_reference: Difficulty reference (e.g., Oxford3000_B1_B2)
        
        Returns:
            List of dictionaries containing word data
        """
        prompt = self._build_vocabulary_prompt(user_profile, word_count, difficulty_reference)
        prompt_hash = self._hash_text(prompt)
        
        try:
            response = await self._call_llm(prompt)
            response_hash = self._hash_text(str(response))
            
            # Parse the response
            vocabulary_data = self._parse_vocabulary_response(response)
            
            # Add metadata to each word
            for word_data in vocabulary_data:
                word_data.update({
                    "llm_provider": self.provider,
                    "llm_model": self._get_model_name(),
                    "llm_prompt_hash": prompt_hash,
                    "llm_response_hash": response_hash,
                    "difficulty_level": difficulty_reference.replace("Oxford3000_", "")
                })
            
            logger.info(f"Generated {len(vocabulary_data)} words using {self.provider}")
            return vocabulary_data
            
        except Exception as e:
            logger.error(f"Failed to generate vocabulary: {e}")
            # Return mock data in case of error
            return self._generate_mock_vocabulary(word_count, difficulty_reference)
    
    def _build_vocabulary_prompt(
        self,
        user_profile: Dict[str, Any],
        word_count: int,
        difficulty_reference: str
    ) -> str:
        """Build the prompt for vocabulary generation."""
        difficulty_level = difficulty_reference.replace("Oxford3000_", "")
        
        prompt = f"""
You are an expert English vocabulary teacher. Generate {word_count} English vocabulary words suitable for intermediate learners (level {difficulty_level}).

Requirements:
1. Words should be from the Oxford 3000 wordlist at {difficulty_level} level
2. Provide Turkish translations
3. Include part of speech
4. Generate 2-3 unique example sentences for each word
5. Provide Turkish translations for all example sentences
6. Ensure words are useful for daily communication

User Context:
- Difficulty Level: {user_profile.get('difficulty_level', difficulty_level)}
- Language: Turkish (native) learning English

Please respond with a JSON array where each object has this structure:
{{
    "english_word": "example",
    "turkish_translation": "örnek",
    "part_of_speech": "noun",
    "definition": "a thing characteristic of its kind or illustrating a general rule",
    "examples": [
        {{
            "english_sentence": "Can you give me an example?",
            "turkish_translation": "Bana bir örnek verebilir misin?"
        }},
        {{
            "english_sentence": "This is a perfect example of good teamwork.",
            "turkish_translation": "Bu, iyi takım çalışmasının mükemmel bir örneğidir."
        }}
    ]
}}

Generate exactly {word_count} words. Focus on practical, commonly used vocabulary.
"""
        return prompt.strip()
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM provider."""
        for attempt in range(self.max_retries):
            try:
                if self.provider == "openai":
                    return await self._call_openai(prompt)
                elif self.provider == "google":
                    return await self._call_google(prompt)
                else:  # mock
                    return await self._call_mock(prompt)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        if not self._openai_client:
            raise ValueError("OpenAI client not initialized")
        
        response = await self._openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful English vocabulary teacher."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    async def _call_google(self, prompt: str) -> str:
        """Call Google AI API."""
        if not self._google_client:
            raise ValueError("Google AI client not initialized")
        
        response = await self._google_client.generate_content_async(prompt)
        return response.text
    
    async def _call_mock(self, prompt: str) -> str:
        """Mock LLM response for testing."""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        # Extract word count from prompt
        word_count = 5  # default
        if "Generate exactly" in prompt:
            try:
                word_count = int(prompt.split("Generate exactly")[1].split("words")[0].strip())
            except:
                pass
        
        mock_words = [
            {
                "english_word": "journey",
                "turkish_translation": "yolculuk",
                "part_of_speech": "noun",
                "definition": "an act of traveling from one place to another",
                "examples": [
                    {
                        "english_sentence": "The journey took three hours.",
                        "turkish_translation": "Yolculuk üç saat sürdü."
                    },
                    {
                        "english_sentence": "Life is a long journey.",
                        "turkish_translation": "Hayat uzun bir yolculuktur."
                    }
                ]
            },
            {
                "english_word": "comfortable",
                "turkish_translation": "rahat",
                "part_of_speech": "adjective",
                "definition": "giving a feeling of physical relaxation",
                "examples": [
                    {
                        "english_sentence": "This chair is very comfortable.",
                        "turkish_translation": "Bu sandalye çok rahat."
                    },
                    {
                        "english_sentence": "I feel comfortable in this room.",
                        "turkish_translation": "Bu odada kendimi rahat hissediyorum."
                    }
                ]
            }
        ]
        
        # Repeat words to match requested count
        result = []
        for i in range(word_count):
            word = mock_words[i % len(mock_words)].copy()
            if i >= len(mock_words):
                word["english_word"] = f"{word['english_word']}_{i}"
            result.append(word)
        
        return json.dumps(result, ensure_ascii=False)
    
    def _parse_vocabulary_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the LLM response into structured vocabulary data."""
        try:
            # Try to parse as JSON
            data = json.loads(response)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "words" in data:
                return data["words"]
            else:
                raise ValueError("Invalid response format")
        except json.JSONDecodeError:
            # Try to extract JSON from response if it's wrapped in text
            start = response.find('[')
            end = response.rfind(']') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("Could not parse LLM response as JSON")
    
    def _generate_mock_vocabulary(self, word_count: int, difficulty_reference: str) -> List[Dict[str, Any]]:
        """Generate mock vocabulary data as fallback."""
        logger.warning("Using mock vocabulary data")
        mock_response = asyncio.run(self._call_mock(f"Generate exactly {word_count} words"))
        return self._parse_vocabulary_response(mock_response)
    
    def _get_model_name(self) -> str:
        """Get the current model name."""
        if self.provider == "openai":
            return settings.openai_model
        elif self.provider == "google":
            return settings.google_ai_model
        else:
            return "mock"
    
    def _hash_text(self, text: str) -> str:
        """Generate SHA-256 hash of text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    async def generate_quiz_questions(
        self,
        words: List[Dict[str, Any]],
        question_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions for given words."""
        if question_types is None:
            question_types = ["multiple_choice", "fill_blank", "translation"]
        
        # This is a placeholder for quiz generation
        # Can be implemented similar to vocabulary generation
        logger.info(f"Quiz generation requested for {len(words)} words")
        return []
    
    async def verify_content_quality(self, content: Dict[str, Any]) -> float:
        """Verify the quality of generated content."""
        # This is a placeholder for content quality verification
        # Could use another LLM call to rate the quality
        return 0.8  # Mock quality score 