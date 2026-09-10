"""Dog profile endpoints. Ownership is enforced server-side."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.serializers import dog_to_read
from app.db.models import User
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.schemas.dogs import DogCreate, DogRead, DogUpdate
from app.services.dogs import DogService

router = APIRouter(tags=["dogs"])


@router.get("", response_model=list[DogRead], summary="List the user's dogs")
async def list_dogs(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[DogRead]:
    dogs = await DogService(session).list_for_user(user.id)
    return [dog_to_read(dog) for dog in dogs]


@router.post(
    "",
    response_model=DogRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a dog profile",
)
async def create_dog(
    payload: DogCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DogRead:
    dog = await DogService(session).create(user.id, payload)
    await session.commit()
    return dog_to_read(dog)


@router.get("/{dog_id}", response_model=DogRead, summary="Get a dog profile")
async def get_dog(
    dog_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DogRead:
    dog = await DogService(session).get_for_user(user.id, dog_id)
    return dog_to_read(dog)


@router.patch("/{dog_id}", response_model=DogRead, summary="Update a dog profile")
async def update_dog(
    dog_id: uuid.UUID,
    payload: DogUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DogRead:
    dog = await DogService(session).update(user.id, dog_id, payload)
    await session.commit()
    return dog_to_read(dog)


@router.delete("/{dog_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a dog profile")
async def delete_dog(
    dog_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Response:
    await DogService(session).delete(user.id, dog_id)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
