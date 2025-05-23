"""
Tests for LLM service functionality.
"""

import pytest
from app.llm_interface.llm_service import LLMService


class TestLLMService:
    """Test cases for LLMService."""
    
    @pytest.mark.asyncio
    async def test_mock_vocabulary_generation(self):
        """Test vocabulary generation with mock provider."""
        # Arrange
        llm_service = LLMService()
        llm_service.provider = "mock"  # Force mock provider
        
        user_profile = {
            "difficulty_level": "B1_B2",
            "total_words_learned": 0,
            "language_code": "tr"
        }
        
        # Act
        result = await llm_service.generate_vocabulary_set(
            user_profile=user_profile,
            word_count=2,
            difficulty_reference="Oxford3000_B1_B2"
        )
        
        # Assert
        assert len(result) == 2
        assert all("english_word" in word for word in result)
        assert all("turkish_translation" in word for word in result)
        assert all("part_of_speech" in word for word in result)
        assert all("examples" in word for word in result)
        assert all(word["llm_provider"] == "mock" for word in result)
        assert all(word["difficulty_level"] == "B1_B2" for word in result)
    
    @pytest.mark.asyncio
    async def test_vocabulary_generation_with_examples(self):
        """Test that generated vocabulary includes examples."""
        # Arrange
        llm_service = LLMService()
        llm_service.provider = "mock"
        
        user_profile = {
            "difficulty_level": "B1_B2",
            "total_words_learned": 10,
            "language_code": "tr"
        }
        
        # Act
        result = await llm_service.generate_vocabulary_set(
            user_profile=user_profile,
            word_count=1
        )
        
        # Assert
        word = result[0]
        assert "examples" in word
        assert len(word["examples"]) >= 1
        
        example = word["examples"][0]
        assert "english_sentence" in example
        assert "turkish_translation" in example
        assert len(example["english_sentence"]) > 0
        assert len(example["turkish_translation"]) > 0
    
    def test_hash_text(self):
        """Test text hashing functionality."""
        # Arrange
        llm_service = LLMService()
        test_text = "Hello, world!"
        
        # Act
        hash1 = llm_service._hash_text(test_text)
        hash2 = llm_service._hash_text(test_text)
        hash3 = llm_service._hash_text("Different text")
        
        # Assert
        assert hash1 == hash2  # Same text should produce same hash
        assert hash1 != hash3  # Different text should produce different hash
        assert len(hash1) == 64  # SHA-256 produces 64 character hex string
    
    @pytest.mark.asyncio
    async def test_verify_content_quality(self):
        """Test content quality verification."""
        # Arrange
        llm_service = LLMService()
        sample_content = {
            "english_word": "example",
            "turkish_translation": "örnek",
            "part_of_speech": "noun"
        }
        
        # Act
        quality_score = await llm_service.verify_content_quality(sample_content)
        
        # Assert
        assert isinstance(quality_score, float)
        assert 0.0 <= quality_score <= 1.0
    
    def test_get_model_name(self):
        """Test model name retrieval."""
        # Arrange
        llm_service = LLMService()
        
        # Act & Assert for different providers
        llm_service.provider = "mock"
        assert llm_service._get_model_name() == "mock"
        
        llm_service.provider = "openai"
        model_name = llm_service._get_model_name()
        assert "gpt" in model_name.lower() or model_name == "mock"  # Might fallback to mock
    
    @pytest.mark.asyncio
    async def test_generate_quiz_questions(self):
        """Test quiz question generation (placeholder functionality)."""
        # Arrange
        llm_service = LLMService()
        sample_words = [
            {
                "english_word": "journey",
                "turkish_translation": "yolculuk",
                "part_of_speech": "noun"
            }
        ]
        
        # Act
        quiz_questions = await llm_service.generate_quiz_questions(sample_words)
        
        # Assert
        assert isinstance(quiz_questions, list)
        # Note: Current implementation returns empty list as placeholder 