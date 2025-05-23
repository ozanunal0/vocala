"""
Base repository class with common CRUD operations.
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def create(self, **kwargs) -> T:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """Get record by ID."""
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all records with pagination."""
        result = await self.db.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_by_filter(self, **filters) -> List[T]:
        """Get records by filter criteria."""
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_first_by_filter(self, **filters) -> Optional[T]:
        """Get first record matching filter criteria."""
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_by_id(self, id: int, **kwargs) -> Optional[T]:
        """Update record by ID."""
        await self.db.execute(
            update(self.model).where(self.model.id == id).values(**kwargs)
        )
        await self.db.commit()
        return await self.get_by_id(id)
    
    async def delete_by_id(self, id: int) -> bool:
        """Delete record by ID."""
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.db.commit()
        return result.rowcount > 0
    
    async def count(self, **filters) -> int:
        """Count records with optional filters."""
        query = select(func.count(self.model.id))
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await self.db.execute(query)
        return result.scalar()
    
    async def exists(self, **filters) -> bool:
        """Check if record exists with given filters."""
        count = await self.count(**filters)
        return count > 0
    
    async def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records."""
        instances = [self.model(**item) for item in items]
        self.db.add_all(instances)
        await self.db.commit()
        
        # Refresh all instances to get generated IDs
        for instance in instances:
            await self.db.refresh(instance)
        
        return instances
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Update multiple records. Each dict should contain 'id' and update fields."""
        count = 0
        for update_data in updates:
            if "id" not in update_data:
                continue
            
            record_id = update_data.pop("id")
            if update_data:  # Only update if there are fields to update
                await self.db.execute(
                    update(self.model).where(self.model.id == record_id).values(**update_data)
                )
                count += 1
        
        await self.db.commit()
        return count 