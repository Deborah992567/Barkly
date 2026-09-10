"""Dog persistence with ownership-scoped lookups.

All queries are scoped by owner id so routes can never read other users' dogs
even if a route accidentally omits a check.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dog
from app.schemas.dogs import DogCreate


class DogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Dog]:
        stmt = (
            select(Dog).where(Dog.owner_id == owner_id).order_by(Dog.created_at.asc(), Dog.id.asc())
        )
        return list((await self._session.execute(stmt)).scalars())

    async def get_by_id_and_owner(self, dog_id: uuid.UUID, owner_id: uuid.UUID) -> Dog | None:
        stmt = select(Dog).where(Dog.id == dog_id, Dog.owner_id == owner_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def create(self, owner_id: uuid.UUID, payload: DogCreate) -> Dog:
        dog = Dog(
            owner_id=owner_id,
            name=payload.name.strip(),
            breed=payload.breed,
            sex=payload.sex.value if payload.sex else None,
            date_of_birth=payload.date_of_birth,
            notes=payload.notes,
        )
        self._session.add(dog)
        await self._session.flush()
        return dog

    async def update(self, dog: Dog, changes: dict) -> Dog:
        for field, value in changes.items():
            if field == "sex" and value is not None:
                value = value.value
            setattr(dog, field, value)
        await self._session.flush()
        return dog

    async def delete(self, dog: Dog) -> None:
        await self._session.delete(dog)
        await self._session.flush()
