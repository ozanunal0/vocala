"""
Word management service - primary consumer of LLMService.
Handles caching and retrieval of LLM-generated vocabulary.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.word import Word
from app.db.models.example import Example
from app.db.repositories.word import WordRepository
from app.db.repositories.example import ExampleRepository
from app.llm_interface.llm_service import LLMService

logger = logging.getLogger(__name__)


class WordManagementService:
    """Service for managing vocabulary words and LLM integration."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.word_repo = WordRepository(db)
        self.example_repo = ExampleRepository(db)
        self.llm_service = LLMService()
    
    async def get_or_generate_words(
        self,
        user: User,
        word_count: int,
        exclude_word_ids: Optional[List[int]] = None
    ) -> List[Word]:
        """
        Get words from cache or generate new ones if needed.
        This is the main entry point for vocabulary management.
        """
        if exclude_word_ids is None:
            exclude_word_ids = []
        
        # Try to get words from cache first
        cached_words = await self.word_repo.get_verified_words_by_difficulty(
            difficulty_level=user.difficulty_level,
            limit=word_count,
            exclude_word_ids=exclude_word_ids
        )
        
        if len(cached_words) >= word_count:
            logger.info(f"Retrieved {word_count} words from cache for user {user.id}")
            # Mark words as used
            for word in cached_words[:word_count]:
                await self.word_repo.increment_word_usage(word.id)
            return cached_words[:word_count]
        
        # Need to generate more words
        needed_count = word_count - len(cached_words)
        logger.info(f"Need to generate {needed_count} new words for user {user.id}")
        
        try:
            new_words = await self._generate_and_cache_words(user, needed_count)
            all_words = cached_words + new_words
            
            # Mark words as used
            for word in all_words:
                await self.word_repo.increment_word_usage(word.id)
            
            return all_words[:word_count]
            
        except Exception as e:
            logger.error(f"Failed to generate new words: {e}")
            # Return what we have from cache, even if it's less than requested
            return cached_words
    
    async def _generate_and_cache_words(self, user: User, word_count: int) -> List[Word]:
        """Generate new words using LLM and cache them."""
        user_profile = {
            "difficulty_level": user.difficulty_level,
            "total_words_learned": user.total_words_learned,
            "language_code": user.language_code or "tr"
        }
        
        # Generate vocabulary using LLM
        vocabulary_data = await self.llm_service.generate_vocabulary_set(
            user_profile=user_profile,
            word_count=word_count,
            difficulty_reference=f"Oxford3000_{user.difficulty_level}"
        )
        
        # Cache the generated words
        cached_words = []
        for word_data in vocabulary_data:
            try:
                # Check if word already exists
                existing_word = await self.word_repo.get_word_by_text_if_verified(
                    word_data["english_word"]
                )
                
                if existing_word:
                    cached_words.append(existing_word)
                    continue
                
                # Create new word
                word = await self._cache_word_with_examples(word_data)
                cached_words.append(word)
                
            except Exception as e:
                logger.error(f"Failed to cache word {word_data.get('english_word', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully cached {len(cached_words)} new words")
        return cached_words
    
    async def _cache_word_with_examples(self, word_data: Dict[str, Any]) -> Word:
        """Cache a word along with its examples."""
        # Extract word data
        word_info = {
            "english_word": word_data["english_word"],
            "turkish_translation": word_data["turkish_translation"],
            "part_of_speech": word_data["part_of_speech"],
            "llm_provider": word_data["llm_provider"],
            "llm_model": word_data["llm_model"],
            "difficulty_level": word_data["difficulty_level"],
        }
        
        # Optional fields
        if "definition" in word_data:
            word_info["definition"] = word_data["definition"]
        if "pronunciation" in word_data:
            word_info["pronunciation"] = word_data["pronunciation"]
        if "llm_prompt_hash" in word_data:
            word_info["llm_prompt_hash"] = word_data["llm_prompt_hash"]
        if "llm_response_hash" in word_data:
            word_info["llm_response_hash"] = word_data["llm_response_hash"]
        
        # Create the word
        word = await self.word_repo.cache_llm_generated_word(**word_info)
        
        # Cache examples if they exist
        if "examples" in word_data and word_data["examples"]:
            for example_data in word_data["examples"]:
                await self.example_repo.cache_llm_generated_example(
                    word_id=word.id,
                    english_sentence=example_data["english_sentence"],
                    turkish_translation=example_data["turkish_translation"],
                    llm_provider=word_data["llm_provider"],
                    llm_model=word_data["llm_model"],
                    difficulty_level=word_data["difficulty_level"]
                )
        
        return word
    
    async def get_word_with_examples(self, word_id: int) -> Optional[Dict[str, Any]]:
        """Get a word with its examples."""
        word = await self.word_repo.get_by_id(word_id)
        if not word:
            return None
        
        examples = await self.example_repo.get_by_word_id(word_id)
        
        return {
            "word": word.to_dict(),
            "examples": [example.to_dict() for example in examples]
        }
    
    async def search_words(self, search_text: str, limit: int = 20) -> List[Word]:
        """Search for words in the cache."""
        return await self.word_repo.search_words_by_text(
            search_text=search_text,
            verified_only=True,
            limit=limit
        )
    
    async def get_words_for_user_assignment(
        self,
        user: User,
        count: int = 5,
        exclude_word_ids: Optional[List[int]] = None
    ) -> List[Word]:
        """Get words suitable for assignment to a specific user."""
        if exclude_word_ids is None:
            exclude_word_ids = []
        
        return await self.word_repo.get_words_for_user_assignment(
            difficulty_level=user.difficulty_level,
            exclude_word_ids=exclude_word_ids,
            count=count
        )
    
    async def verify_word_quality(self, word_id: int) -> Optional[float]:
        """Verify the quality of a cached word using LLM."""
        word = await self.word_repo.get_by_id(word_id)
        if not word:
            return None
        
        try:
            quality_score = await self.llm_service.verify_content_quality(word.to_dict())
            await self.word_repo.mark_word_as_verified(word_id, quality_score)
            return quality_score
        except Exception as e:
            logger.error(f"Failed to verify word quality for word {word_id}: {e}")
            return None
    
    async def get_unverified_words(self, limit: int = 50) -> List[Word]:
        """Get words that need manual verification."""
        return await self.word_repo.get_words_for_verification(limit)
    
    async def bulk_verify_words(self, word_ids: List[int], verified: bool = True) -> int:
        """Bulk verify/unverify words."""
        count = 0
        for word_id in word_ids:
            result = await self.word_repo.update_by_id(word_id, is_verified=verified)
            if result:
                count += 1
        return count 