"""Repository-level persistence tests (SQLAlchemy session, no HTTP)."""

from __future__ import annotations

import uuid

import pytest_asyncio

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.domain.enums import AnalysisInputType
from app.repositories.analyses import AnalysisRepository, FeedbackRepository
from app.repositories.dogs import DogRepository
from app.repositories.users import UserRepository
from app.schemas.analyses import AnalysisCreateRequest
from app.schemas.dogs import DogCreate


@pytest_asyncio.fixture
async def db_session():
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def _seed_user_and_dog(db_session) -> tuple[uuid.UUID, uuid.UUID]:
    user = await UserRepository(db_session).create(
        email=f"repo-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("a-strong-password!"),
    )
    dog = await DogRepository(db_session).create(user.id, DogCreate(name="Max", breed="Beagle"))
    await db_session.commit()
    return user.id, dog.id


async def test_dog_repository_scopes_ownership(db_session) -> None:
    user_id, dog_id = await _seed_user_and_dog(db_session)
    other_id = uuid.uuid4()
    repo = DogRepository(db_session)
    dog = await repo.get_by_id_and_owner(dog_id, user_id)
    assert dog is not None
    assert dog.name == "Max"
    assert await repo.get_by_id_and_owner(dog_id, other_id) is None


async def test_analysis_creation_and_history(db_session) -> None:
    user_id, dog_id = await _seed_user_and_dog(db_session)
    repo = AnalysisRepository(db_session)
    payload = AnalysisCreateRequest(
        dog_id=dog_id,
        input_type=AnalysisInputType.BEHAVIOR,
        media_ids=[],
        idempotency_key="repo-key-0001",
    )
    analysis = await repo.create(user_id=user_id, dog_id=dog_id, payload=payload)
    await repo.queue(analysis)
    await repo.start_processing(analysis)
    await repo.complete(
        analysis,
        primary_behavior="RELAXED",
        confidence=0.8,
        secondary_behaviors=[],
        detected_audio_category=None,
        explanation="test",
        disclaimer="test",
        provider="test",
        model_name="test",
        model_version="0.0.0",
        is_placeholder=True,
        observations=[],
    )
    await db_session.commit()

    items, total = await repo.list_history(user_id=user_id, page=1, page_size=10)
    assert total == 1
    assert items[0].status == "COMPLETED"
    assert items[0].result is not None

    assert await repo.has_analyses_for_dog(user_id, dog_id) is True


async def test_analysis_idempotency_lookup(db_session) -> None:
    user_id, dog_id = await _seed_user_and_dog(db_session)
    repo = AnalysisRepository(db_session)
    payload = AnalysisCreateRequest(
        dog_id=dog_id,
        input_type=AnalysisInputType.BEHAVIOR,
        media_ids=[],
        idempotency_key="repo-idem-0001",
    )
    first = await repo.create(user_id=user_id, dog_id=dog_id, payload=payload)
    await db_session.commit()
    existing = await repo.get_by_idempotency(user_id, "repo-idem-0001")
    assert existing is not None
    assert existing.id == first.id


async def test_feedback_preserves_prediction(db_session) -> None:
    user_id, dog_id = await _seed_user_and_dog(db_session)
    repo = AnalysisRepository(db_session)
    payload = AnalysisCreateRequest(
        dog_id=dog_id, input_type=AnalysisInputType.BEHAVIOR, media_ids=[]
    )
    analysis = await repo.create(user_id=user_id, dog_id=dog_id, payload=payload)
    await repo.complete(
        analysis,
        primary_behavior="PLAYFUL",
        confidence=0.7,
        secondary_behaviors=[],
        detected_audio_category=None,
        explanation="x",
        disclaimer="x",
        provider="p",
        model_name="m",
        model_version="1",
        is_placeholder=True,
        observations=[],
    )
    await db_session.commit()

    feedback = await FeedbackRepository(db_session).create(
        analysis=analysis,
        user_id=user_id,
        verdict="CORRECTED",
        predicted_behavior="PLAYFUL",
        corrected_behavior="ALERT",
        comment="nope",
    )
    await db_session.commit()
    assert feedback.predicted_behavior == "PLAYFUL"
    assert feedback.corrected_behavior == "ALERT"
    assert repr(feedback.analysis_id) == repr(analysis.id)
