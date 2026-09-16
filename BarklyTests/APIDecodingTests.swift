import XCTest
@testable import Barkly

final class APIDecodingTests: XCTestCase {

    private var decoder: JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }

    func testTokenResponseDecodes() throws {
        let json = """
        {
            "access_token": "abc123",
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": "11111111-1111-1111-1111-111111111111",
                "email": "a@b.com",
                "display_name": null,
                "created_at": "2026-01-01T00:00:00Z"
            }
        }
        """
        let dto = try decoder.decode(TokenResponseDTO.self, from: Data(json.utf8))
        XCTAssertEqual(dto.accessToken, "abc123")
        XCTAssertEqual(dto.expiresIn, 86400)
        XCTAssertEqual(dto.user.email, "a@b.com")
        XCTAssertNil(dto.user.displayName)
    }

    func testDogDTODecodesWithOptionalFields() throws {
        let json = """
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "name": "Max",
            "breed": null,
            "sex": null,
            "date_of_birth": null,
            "notes": "Friendly",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"
        }
        """
        let dto = try decoder.decode(DogDTO.self, from: Data(json.utf8))
        XCTAssertEqual(dto.name, "Max")
        let dog = Dog(dto: dto)
        XCTAssertEqual(dog.name, "Max")
        XCTAssertEqual(dog.breed, "")
    }

    func testAnalysisDTODecodesAndMapsToDomain() throws {
        let json = """
        {
            "analysis_id": "22222222-2222-2222-2222-222222222222",
            "dog_id": "11111111-1111-1111-1111-111111111111",
            "status": "COMPLETED",
            "input_type": "AUDIO",
            "created_at": "2026-09-10T12:00:00Z",
            "started_at": "2026-09-10T12:00:01Z",
            "completed_at": "2026-09-10T12:00:05Z",
            "media": [],
            "result": {
                "primary_behavior": "PLAYFUL",
                "confidence": 0.75,
                "secondary_behaviors": ["EXCITED"],
                "detected_audio_category": "BARK",
                "observations": [
                    {"category": "AUDIO", "description": "Periodic vocalization bursts"}
                ],
                "explanation": "Playful posture and bouncy movement.",
                "disclaimer": "Not a diagnosis.",
                "provider": "barkly-models",
                "model_name": "fusion-v1",
                "model_version": "barkly-fusion-1.0.0",
                "is_placeholder": false,
                "generated_at": "2026-09-10T12:00:05Z",
                "is_insufficient_evidence": false
            }
        }
        """
        let dto = try decoder.decode(AnalysisDTO.self, from: Data(json.utf8))
        XCTAssertEqual(dto.inputType, "AUDIO")
        let analysis = BehaviorAnalysis(dto: dto)
        XCTAssertEqual(analysis.estimatedState, .playful)
        XCTAssertEqual(analysis.confidence, 0.75, accuracy: 0.0001)
        XCTAssertEqual(analysis.secondaryBehaviors, [.excited])
        XCTAssertEqual(analysis.observations, ["Periodic vocalization bursts"])
        XCTAssertEqual(analysis.modelName, "fusion-v1")
    }

    func testBehaviorStateWireMapping() {
        XCTAssertEqual(BehaviorState(apiValue: "RELAXED"), .calm)
        XCTAssertEqual(BehaviorState(apiValue: "ATTENTION_SEEKING"), .attentionSeeking)
        XCTAssertEqual(BehaviorState(apiValue: "STRESSED"), .unknown)
        XCTAssertEqual(BehaviorState.calm.apiValue, "RELAXED")
    }

    func testAnalysisInputTypeWireMapping() {
        XCTAssertEqual(AnalysisInputType.audio.apiValue, "AUDIO")
        XCTAssertEqual(AnalysisInputType.photo.apiValue, "IMAGE")
        XCTAssertEqual(AnalysisInputType(apiValue: "VIDEO"), .video)
        XCTAssertNil(AnalysisInputType(apiValue: "BOGUS"))
    }

    func testHistoryPageDecodes() throws {
        let json = """
        {
            "items": [],
            "page": 1,
            "page_size": 20,
            "total": 0,
            "has_next": false
        }
        """
        let dto = try decoder.decode(HistoryPageDTO.self, from: Data(json.utf8))
        let page = HistoryPage(dto: dto)
        XCTAssertTrue(page.isEmpty)
        XCTAssertEqual(page.page, 1)
        XCTAssertFalse(page.hasNext)
    }
}