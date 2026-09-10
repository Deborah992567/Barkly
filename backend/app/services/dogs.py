"""Dog profile service: CRUD with ownership enforcement.

Deleting a dog with analysis history is rejected (409) rather than silently
destroying historical behavioral records.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode, conflict_error, not_found_error
from app.db.models import Dog
from app.repositories.analyses import AnalysisRepository
from app.repositories.dogs import DogRepository
from app.schemas.dogs import DogCreate, DogUpdate


class DogService:
    def __init__(self, session: AsyncSession) -> None:
        self._dogs = DogRepository(session)
        self._analyses = AnalysisRepository(session)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Dog]:
        return await self._dogs.list_by_owner(user_id)

    async def get_for_user(self, user_id: uuid.UUID, dog_id: uuid.UUID) -> Dog:
        dog = await self._dogs.get_by_id_and_owner(dog_id, user_id)
        if dog is None:
            raise not_found_error(ErrorCode.DOG_NOT_FOUND, "The requested dog could not be found.")
        return dog

    async def create(self, user_id: uuid.UUID, payload: DogCreate) -> Dog:
        return await self._dogs.create(user_id, payload)

    async def update(self, user_id: uuid.UUID, dog_id: uuid.UUID, payload: DogUpdate) -> Dog:
        dog = await self.get_for_user(user_id, dog_id)
        changes = payload.model_dump(exclude_unset=True)
        return await self._dogs.update(dog, changes)

    async def delete(self, user_id: uuid.UUID, dog_id: uuid.UUID) -> None:
        dog = await self.get_for_user(user_id, dog_id)
        if await self._analyses.has_analyses_for_dog(user_id, dog_id):
            raise conflict_error("This dog cannot be deleted while analysis history exists.")
        await self._dogs.delete(dog)
