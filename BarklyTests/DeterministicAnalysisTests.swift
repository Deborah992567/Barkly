import XCTest
@testable import Barkly

final class DeterministicAnalysisTests: XCTestCase {

    func testRepeatedAudioAnalysisIsIdentical() async throws {
        let repository = MockAnalysisRepository(latency: 0)
        let first = try await repository.requestAnalysis(
            for: MockSeeds.max.id,
            inputType: .audio,
            vocalizationType: nil,
            duration: 4
        )
        let second = try await repository.requestAnalysis(
            for: MockSeeds.max.id,
            inputType: .audio,
            vocalizationType: nil,
            duration: 4
        )
        XCTAssertEqual(first.estimatedState, second.estimatedState)
        XCTAssertEqual(first.confidence, second.confidence)
        XCTAssertEqual(first.observations, second.observations)
        XCTAssertEqual(first.explanation, second.explanation)
    }

    func testPhotoAnalysisNeverReportsAudioState() async throws {
        let repository = MockAnalysisRepository(latency: 0)
        let analysis = try await repository.requestAnalysis(
            for: MockSeeds.max.id,
            inputType: .photo,
            vocalizationType: nil,
            duration: nil
        )
        XCTAssertEqual(analysis.estimatedState, .calm)
        XCTAssertNil(analysis.vocalizationType)
    }

    func testAnalysisExplanationMentionsDogName() async throws {
        let repository = MockAnalysisRepository(latency: 0)
        let analysis = try await repository.requestAnalysis(
            for: MockSeeds.max.id,
            inputType: .behavior,
            vocalizationType: nil,
            duration: nil
        )
        XCTAssertTrue(analysis.explanation.contains("Max"))
    }
}