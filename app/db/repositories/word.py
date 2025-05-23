"""Word repository for managing LLM-generated vocabulary cache."""

from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.word import Word
from app.db.repositories.base import BaseRepository


class WordRepository(BaseRepository[Word]):
    """Repository for Word model with LLM cache management."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Word, db)
    
    async def get_word_by_text_if_verified(self, english_word: str) -> Optional[Word]:
        """Get word by English text if it's verified."""
        result = await self.db.execute(
            select(Word).where(
                and_(
                    func.lower(Word.english_word) == english_word.lower(),
                    Word.is_verified == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def cache_llm_generated_word(
        self,
        english_word: str,
        turkish_translation: str,
        part_of_speech: str,
        llm_provider: str,
        llm_model: str,
        difficulty_level: str = "B1_B2",
        **kwargs
    ) -> Word:
        """Cache a new LLM-generated word."""
        word_data = {
            "english_word": english_word.strip(),
            "turkish_translation": turkish_translation.strip(),
            "part_of_speech": part_of_speech.strip(),
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "difficulty_level": difficulty_level,
            **kwargs
        }
        return await self.create(**word_data)
    
    async def get_verified_words_by_difficulty(
        self, 
        difficulty_level: str, 
        limit: int = 100,
        exclude_word_ids: Optional[List[int]] = None
    ) -> List[Word]:
        """Get verified words by difficulty level."""
        query = select(Word).where(
            and_(
                Word.difficulty_level == difficulty_level,
                Word.is_verified == True
            )
        )
        
        if exclude_word_ids:
            query = query.where(Word.id.notin_(exclude_word_ids))
        
        query = query.order_by(Word.usage_count.asc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def increment_word_usage(self, word_id: int) -> None:
        """Increment usage count for a word."""
        word = await self.get_by_id(word_id)
        if word:
            word.increment_usage()
            await self.db.commit() 