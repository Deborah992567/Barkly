"""Service-layer tests: dog ownership, analysis lifecycle, feedback rules."""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from app.ai.base import ProviderUnavailableError
from app.ai.types import AnalysisInput, InferenceResult
from app.core.errors import ErrorCode
from app.db.session import get_session_factory
from app.domain.enums import AnalysisInputType, BehaviorState
from app.domain.value_objects import ModelIdentity
from app.repositories.users import UserRepository
from app.schemas.analyses import AnalysisCreateRequest
from app.schemas.dogs import DogCreate, DogUpdate
from app.schemas.feedback import FeedbackCreate
from app.services.analyses import AnalysisService
from app.services.dogs import DogService
from app.services.feedback import FeedbackService


@pytest_asyncio.fixture
async def db_session():
    factory = get_session_factory()
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def user(db_session):
    user = await UserRepository(db_session).create(
        email=f"svc-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="not-used-in-tests",
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def dog(user, db_session) -> uuid.UUID:
    dog = await DogService(db_session).create(user.id, DogCreate(name="Max"))
    await db_session.commit()
    return dog.id


async def test_dog_service_rejects_cross_user_access(db_session, user, dog) -> None:
    service = DogService(db_session)
    with pytest.raises(Exception) as exc:
        await service.get_for_user(uuid.uuid4(), dog)
    assert exc.value.code == ErrorCode.DOG_NOT_FOUND


async def test_dog_service_update(db_session, user, dog) -> None:
    updated = await DogService(db_session).update(
        user.id, dog, DogUpdate(name="Bella", breed="Poodle")
    )
    await db_session.commit()
    assert updated.name == "Bella"
    assert updated.breed == "Poodle"


async def test_analysis_service_creates_completed(db_session, user, dog) -> None:
    payload = AnalysisCreateRequest(
        dog_id=dog,
        input_type=AnalysisInputType.BEHAVIOR,
        media_ids=[],
        idempotency_key="svc-key-0001",
    )
    analysis = await AnalysisService(db_session).create(user.id, payload)
    await db_session.commit()
    assert analysis.status == "COMPLETED"
    assert analysis.result is not None
    assert analysis.result.provider == "development-placeholder"
    assert analysis.result.is_placeholder is True
    assert analysis.result.primary_behavior in {s.value for s in BehaviorState}


async def test_analysis_service_rejects_missing_dog(db_session, user) -> None:
    payload = AnalysisCreateRequest(
        dog_id=uuid.uuid4(),
        input_type=AnalysisInputType.BEHAVIOR,
        media_ids=[],
    )
    service = AnalysisService(db_session)
    request = payload
    # monkeypatch-free: dog simply does not exist for this user
    with pytest.raises(Exception) as exc:
        await service.create(user.id, request)
    assert exc.value.code == ErrorCode.DOG_NOT_FOUND


async def test_analysis_service_marks_failed_on_provider_error(
    db_session, user, dog, monkeypatch
) -> None:
    class FailingProvider:
        identity = ModelIdentity(
            provider="test", model_name="failing", model_version="0.0.0-test", is_placeholder=True
        )

        async def analyze(self, request: AnalysisInput) -> InferenceResult:
            raise ProviderUnavailableError("down")

        async def health(self) -> bool:
            return True

    monkeypatch.setattr("app.services.analyses.get_provider", lambda name: FailingProvider())
    payload = AnalysisCreateRequest(
        dog_id=dog,
        input_type=AnalysisInputType.BEHAVIOR,
        media_ids=[],
    )
    analysis = await AnalysisService(db_session).create(user.id, payload)
    await db_session.commit()
    assert analysis.status == "FAILED"
    assert analysis.failure_code == "PROVIDER_UNAVAILABLE"
    assert analysis.result is None


async def test_feedback_service_requires_completed(db_session, user, dog) -> None:
    payload = AnalysisCreateRequest(
        dog_id=dog,
        input_type=AnalysisInputType.BEHAVIOR,
        media_ids=[],
        idempotency_key="svc-key-0002",
    )
    analysis = await AnalysisService(db_session).create(user.id, payload)
    await db_session.commit()
    feedback = await FeedbackService(db_session).submit(
        user.id,
        analysis,
        FeedbackCreate(
            verdict="CORRECTED",
            corrected_behavior=BehaviorState.ALERT,
        ),
    )
    await db_session.commit()
    assert feedback.predicted_behavior == analysis.result.primary_behavior
    assert feedback.corrected_behavior == "ALERT"
