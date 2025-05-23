"""Notion service for integrating with Notion databases."""

import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotionService:
    """Service for Notion integration."""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Notion client if API key is available."""
        if settings.notion_api_key:
            try:
                from notion_client import AsyncClient
                self.client = AsyncClient(auth=settings.notion_api_key)
                logger.info("Notion client initialized")
            except ImportError:
                logger.error("Notion client package not installed")
            except Exception as e:
                logger.error(f"Failed to initialize Notion client: {e}")
        else:
            logger.info("Notion API key not provided, service disabled")
    
    async def create_vocabulary_page(
        self,
        database_id: str,
        word_data: Dict[str, Any],
        user_notion_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new page in a Notion database for a vocabulary word.
        
        Args:
            database_id: Notion database ID
            word_data: Word information including english_word, turkish_translation, etc.
            user_notion_token: User-specific Notion token (if different from global)
        
        Returns:
            Created page data or None if failed
        """
        if not self._is_available():
            logger.warning("Notion service not available")
            return None
        
        try:
            # Use user-specific token if provided
            client = self.client
            if user_notion_token:
                from notion_client import AsyncClient
                client = AsyncClient(auth=user_notion_token)
            
            # Get database info to find property types and names
            db_info = await client.databases.retrieve(database_id=database_id)
            db_properties = db_info.get("properties", {})
            
            # Prepare page properties based on actual database schema
            properties = self._build_adaptive_page_properties(word_data, db_properties)
            
            # Create the page
            response = await client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            
            logger.info(f"Created Notion page for word: {word_data.get('english_word')}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            return None
    
    def _build_page_properties(self, word_data: Dict[str, Any], title_property_name: str = "Word") -> Dict[str, Any]:
        """Build Notion page properties from word data."""
        properties = {}
        
        # English word (title) - use provided title property name
        if "english_word" in word_data:
            properties[title_property_name] = {
                "title": [
                    {
                        "text": {
                            "content": word_data["english_word"]
                        }
                    }
                ]
            }
        
        # Turkish translation
        if "turkish_translation" in word_data:
            properties["Turkish Translation"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": word_data["turkish_translation"]
                        }
                    }
                ]
            }
        
        # Part of speech
        if "part_of_speech" in word_data:
            properties["Part of Speech"] = {
                "select": {
                    "name": word_data["part_of_speech"]
                }
            }
        
        # Definition
        if "definition" in word_data and word_data["definition"]:
            properties["Definition"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": word_data["definition"]
                        }
                    }
                ]
            }
        
        # Difficulty level
        if "difficulty_level" in word_data:
            properties["Level"] = {
                "select": {
                    "name": word_data["difficulty_level"]
                }
            }
        
        # Examples (as rich text)
        if "examples" in word_data and word_data["examples"]:
            examples_text = ""
            for i, example in enumerate(word_data["examples"][:3], 1):  # Limit to 3 examples
                examples_text += f"{i}. {example.get('english_sentence', '')}\n"
                examples_text += f"   {example.get('turkish_translation', '')}\n\n"
            
            if examples_text:
                properties["Examples"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": examples_text.strip()
                            }
                        }
                    ]
                }
        
        # Add current date
        from datetime import datetime
        properties["Date Added"] = {
            "date": {
                "start": datetime.now().isoformat()[:10]  # YYYY-MM-DD format
            }
        }
        
        # Mastered defaults to false
        properties["Mastered"] = {
            "checkbox": False
        }
        
        return properties
    
    def _build_adaptive_page_properties(self, word_data: Dict[str, Any], db_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Build Notion page properties adapted to the actual database schema."""
        properties = {}
        
        # Find title property and set English word
        title_prop = None
        for prop_name, prop_info in db_properties.items():
            if prop_info.get("type") == "title":
                title_prop = prop_name
                break
        
        if title_prop and "english_word" in word_data:
            properties[title_prop] = {
                "title": [
                    {
                        "text": {
                            "content": word_data["english_word"]
                        }
                    }
                ]
            }
        
        # Map our data to database properties based on their actual types
        property_mappings = {
            "Turkish Translation": "turkish_translation",
            "Part of Speech": "part_of_speech", 
            "Definition": "definition",
            "Level": "difficulty_level",
            "Examples": "examples"
        }
        
        for db_prop_name, data_key in property_mappings.items():
            if db_prop_name in db_properties and data_key in word_data:
                prop_type = db_properties[db_prop_name].get("type")
                value = word_data[data_key]
                
                if prop_type == "rich_text" and value:
                    # Handle examples specially (they're a list)
                    if data_key == "examples" and isinstance(value, list):
                        examples_text = ""
                        for i, example in enumerate(value[:3], 1):
                            if isinstance(example, dict):
                                examples_text += f"{i}. {example.get('english_sentence', '')}\n"
                                examples_text += f"   {example.get('turkish_translation', '')}\n\n"
                        value = examples_text.strip()
                    
                    properties[db_prop_name] = {
                        "rich_text": [
                            {
                                "text": {
                                    "content": str(value)
                                }
                            }
                        ]
                    }
                
                elif prop_type == "select" and value:
                    properties[db_prop_name] = {
                        "select": {
                            "name": str(value)
                        }
                    }
        
        # Add optional properties if they exist in the database
        optional_properties = {
            "Date Added": "date",
            "Mastered": "checkbox"
        }
        
        for prop_name, prop_type in optional_properties.items():
            if prop_name in db_properties:
                if prop_type == "date":
                    from datetime import datetime
                    properties[prop_name] = {
                        "date": {
                            "start": datetime.now().isoformat()[:10]
                        }
                    }
                elif prop_type == "checkbox":
                    properties[prop_name] = {
                        "checkbox": False
                    }
        
        return properties
    
    async def test_database_access(
        self,
        database_id: str,
        user_notion_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Test if the database can be accessed and check its schema.
        
        Args:
            database_id: Notion database ID to test
            user_notion_token: User-specific Notion token
        
        Returns:
            Dict with access status and schema info
        """
        result = {
            "accessible": False,
            "has_required_properties": False,
            "missing_properties": [],
            "database_name": "",
            "error": None
        }
        
        if not self._is_available():
            result["error"] = "Notion service not available"
            return result
        
        try:
            # Use user-specific token if provided
            client = self.client
            if user_notion_token:
                from notion_client import AsyncClient
                client = AsyncClient(auth=user_notion_token)
            
            # Try to retrieve database info
            response = await client.databases.retrieve(database_id=database_id)
            
            result["accessible"] = True
            result["database_name"] = response.get('title', [{}])[0].get('plain_text', 'Unknown')
            
            # Check for required properties
            existing_properties = response.get("properties", {})
            
            # Check if there's already a title property (we'll use it instead of creating "Word")
            existing_title = None
            for prop_name, prop_info in existing_properties.items():
                if prop_info.get("type") == "title":
                    existing_title = prop_name
                    break
            
            # Core properties we want (flexible about types)
            desired_properties = [
                "Turkish Translation", "Part of Speech", 
                "Definition", "Level", "Examples"
            ]
            
            # Only require "Word" title if no title exists
            if not existing_title:
                desired_properties.insert(0, "Word")
            
            # Check what's missing (but be flexible - any property type is OK)
            missing = []
            compatible_properties = []
            
            for prop in desired_properties:
                if prop not in existing_properties:
                    missing.append(prop)
                else:
                    # Property exists, note its type for compatibility
                    prop_type = existing_properties[prop].get("type", "unknown")
                    compatible_properties.append(f"{prop} ({prop_type})")
            
            # Consider it "compatible" if we have most core properties
            core_exists = len([p for p in ["Turkish Translation", "Definition"] if p in existing_properties])
            is_usable = existing_title is not None and core_exists >= 1
            
            result["missing_properties"] = missing
            result["has_required_properties"] = len(missing) <= 2  # Allow some missing
            result["is_usable"] = is_usable
            result["existing_title_property"] = existing_title
            result["compatible_properties"] = compatible_properties
            
            logger.info(f"Database access test: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to access Notion database {database_id}: {e}")
            result["error"] = str(e)
            return result
    
    async def create_vocabulary_database(
        self,
        parent_page_id: str,
        database_name: str = "Vocala Vocabulary",
        user_notion_token: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a new database for vocabulary in Notion.
        
        Args:
            parent_page_id: Parent page ID where database will be created
            database_name: Name for the new database
            user_notion_token: User-specific Notion token
        
        Returns:
            Database ID if created successfully, None otherwise
        """
        if not self._is_available():
            return None
        
        try:
            # Use user-specific token if provided
            client = self.client
            if user_notion_token:
                from notion_client import AsyncClient
                client = AsyncClient(auth=user_notion_token)
            
            # Define database schema
            properties = {
                "Word": {"title": {}},
                "Turkish Translation": {"rich_text": {}},
                "Part of Speech": {
                    "select": {
                        "options": [
                            {"name": "noun", "color": "blue"},
                            {"name": "verb", "color": "green"},
                            {"name": "adjective", "color": "yellow"},
                            {"name": "adverb", "color": "orange"},
                            {"name": "preposition", "color": "red"},
                            {"name": "conjunction", "color": "purple"},
                            {"name": "pronoun", "color": "pink"},
                            {"name": "interjection", "color": "gray"}
                        ]
                    }
                },
                "Definition": {"rich_text": {}},
                "Level": {
                    "select": {
                        "options": [
                            {"name": "A1", "color": "green"},
                            {"name": "A2", "color": "yellow"},
                            {"name": "B1", "color": "orange"},
                            {"name": "B2", "color": "red"},
                            {"name": "B1_B2", "color": "purple"}
                        ]
                    }
                },
                "Examples": {"rich_text": {}},
                "Date Added": {"date": {}},
                "Mastered": {"checkbox": {}}
            }
            
            # Create the database
            response = await client.databases.create(
                parent={"page_id": parent_page_id},
                title=[{"text": {"content": database_name}}],
                properties=properties
            )
            
            database_id = response["id"]
            logger.info(f"Created Notion vocabulary database: {database_id}")
            return database_id
            
        except Exception as e:
            logger.error(f"Failed to create Notion database: {e}")
            return None
    
    async def bulk_add_words(
        self,
        database_id: str,
        words_data: List[Dict[str, Any]],
        user_notion_token: Optional[str] = None
    ) -> int:
        """
        Add multiple words to Notion database.
        
        Args:
            database_id: Notion database ID
            words_data: List of word data dictionaries
            user_notion_token: User-specific Notion token
        
        Returns:
            Number of words successfully added
        """
        if not self._is_available():
            return 0
        
        success_count = 0
        
        for word_data in words_data:
            result = await self.create_vocabulary_page(
                database_id=database_id,
                word_data=word_data,
                user_notion_token=user_notion_token
            )
            if result:
                success_count += 1
        
        logger.info(f"Successfully added {success_count}/{len(words_data)} words to Notion")
        return success_count
    
    def _is_available(self) -> bool:
        """Check if Notion service is available."""
        return self.client is not None
    
    async def get_database_info(
        self,
        database_id: str,
        user_notion_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get information about a Notion database."""
        if not self._is_available():
            return None
        
        try:
            # Use user-specific token if provided
            client = self.client
            if user_notion_token:
                from notion_client import AsyncClient
                client = AsyncClient(auth=user_notion_token)
            
            response = await client.databases.retrieve(database_id=database_id)
            
            return {
                "id": response["id"],
                "title": response.get("title", [{}])[0].get("plain_text", ""),
                "created_time": response.get("created_time"),
                "last_edited_time": response.get("last_edited_time"),
                "properties": list(response.get("properties", {}).keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return None
    
    async def fix_database_schema(
        self,
        database_id: str,
        user_notion_token: Optional[str] = None
    ) -> bool:
        """
        Add missing properties to an existing database to make it compatible with Vocala.
        
        Args:
            database_id: Notion database ID to fix
            user_notion_token: User-specific Notion token
        
        Returns:
            True if schema was fixed successfully, False otherwise
        """
        if not self._is_available():
            return False
        
        try:
            # Use user-specific token if provided
            client = self.client
            if user_notion_token:
                from notion_client import AsyncClient
                client = AsyncClient(auth=user_notion_token)
            
            # Check current schema
            test_result = await self.test_database_access(database_id, user_notion_token)
            
            if not test_result["accessible"]:
                logger.error("Cannot access database to fix schema")
                return False
            
            if test_result["has_required_properties"]:
                logger.info("Database already has all required properties")
                return True
            
            # Define property schemas for missing properties
            property_schemas = {
                "Turkish Translation": {"rich_text": {}},
                "Part of Speech": {
                    "select": {
                        "options": [
                            {"name": "noun", "color": "blue"},
                            {"name": "verb", "color": "green"},
                            {"name": "adjective", "color": "yellow"},
                            {"name": "adverb", "color": "orange"},
                            {"name": "preposition", "color": "red"},
                            {"name": "conjunction", "color": "purple"},
                            {"name": "pronoun", "color": "pink"},
                            {"name": "interjection", "color": "gray"}
                        ]
                    }
                },
                "Definition": {"rich_text": {}},
                "Level": {
                    "select": {
                        "options": [
                            {"name": "A1", "color": "green"},
                            {"name": "A2", "color": "yellow"},
                            {"name": "B1", "color": "orange"},
                            {"name": "B2", "color": "red"},
                            {"name": "B1_B2", "color": "purple"}
                        ]
                    }
                },
                "Examples": {"rich_text": {}},
                "Date Added": {"date": {}},
                "Mastered": {"checkbox": {}}
            }
            
            # Only add Word title property if no title exists
            if not test_result.get("existing_title_property"):
                property_schemas["Word"] = {"title": {}}
            
            # Add missing properties one by one
            properties_to_add = {}
            for missing_prop in test_result["missing_properties"]:
                if missing_prop in property_schemas:
                    properties_to_add[missing_prop] = property_schemas[missing_prop]
            
            if properties_to_add:
                # Update database with new properties
                await client.databases.update(
                    database_id=database_id,
                    properties=properties_to_add
                )
                
                logger.info(f"Added {len(properties_to_add)} missing properties to database {database_id}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix database schema: {e}")
            return False 