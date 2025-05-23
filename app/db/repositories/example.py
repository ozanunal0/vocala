"""Example repository for managing LLM-generated example sentences."""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.example import Example
from app.db.repositories.base import BaseRepository


class ExampleRepository(BaseRepository[Example]):
    """Repository for Example model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Example, db)
    
    async def get_by_word_id(self, word_id: int) -> List[Example]:
        """Get all examples for a word."""
        result = await self.db.execute(
            select(Example)
            .where(Example.word_id == word_id)
            .order_by(Example.quality_score.desc().nullslast(), Example.usage_count.asc())
        )
        return list(result.scalars().all())
    
    async def cache_llm_generated_example(
        self,
        word_id: int,
        english_sentence: str,
        turkish_translation: str,
        llm_provider: str,
        llm_model: str,
        **kwargs
    ) -> Example:
        """Cache a new LLM-generated example."""
        example_data = {
            "word_id": word_id,
            "english_sentence": english_sentence.strip(),
            "turkish_translation": turkish_translation.strip(),
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            **kwargs
        }
        return await self.create(**example_data)
    
    async def increment_example_usage(self, example_id: int) -> None:
        """Increment usage count for an example."""
        example = await self.get_by_id(example_id)
        if example:
            example.increment_usage()
            await self.db.commit() 