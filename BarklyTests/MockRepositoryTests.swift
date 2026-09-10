import XCTest
@testable import Barkly

final class MockRepositoryTests: XCTestCase {

    func testMockDogRepositoryFetchesSeededDogs() async throws {
        let repository = MockDogRepository()
        let dogs = try await repository.fetchDogs()
        XCTAssertEqual(dogs.count, 2)
        XCTAssertEqual(dogs.first?.name, "Max")
    }

    func testMockDogRepositoryFetchesByID() async throws {
        let repository = MockDogRepository()
        let dog = try await repository.fetchDog(id: MockSeeds.max.id)
        XCTAssertEqual(dog?.breed, "Golden Retriever")
        let missing = try await repository.fetchDog(id: UUID())
        XCTAssertNil(missing)
    }

    func testMockDogRepositoryUpdatesDog() async throws {
        let repository = MockDogRepository()
        let fetchedDog = try await repository.fetchDog(id: MockSeeds.max.id)
        var updated = try XCTUnwrap(fetchedDog)
        updated.name = "Maxwell"
        try await repository.updateDog(updated)
        let fetched = try await repository.fetchDog(id: MockSeeds.max.id)
        XCTAssertEqual(fetched?.name, "Maxwell")
    }

    func testMockAnalysisIsDeterministicForEachInput() async throws {
        let repository = MockAnalysisRepository(latency: 0)
        let expected: [(AnalysisInputType, BehaviorState, Float)] = [
            (.audio, .attentionSeeking, 0.82),
            (.video, .playful, 0.78),
            (.photo, .calm, 0.74),
            (.behavior, .curious, 0.71)
        ]
        for (input, state, confidence) in expected {
            let analysis = try await repository.requestAnalysis(
                for: MockSeeds.max.id,
                inputType: input,
                vocalizationType: nil,
                duration: nil
            )
            XCTAssertEqual(analysis.estimatedState, state, "state for \(input)")
            XCTAssertEqual(analysis.confidence, confidence, accuracy: 0.0001, "confidence for \(input)")
            XCTAssertEqual(analysis.dogID, MockSeeds.max.id)
        }
    }

    func testMockAnalysisDefaultsAudioVocalizationToBark() async throws {
        let repository = MockAnalysisRepository(latency: 0)
        let analysis = try await repository.requestAnalysis(
            for: MockSeeds.max.id,
            inputType: .audio,
            vocalizationType: nil,
            duration: 3
        )
        XCTAssertEqual(analysis.vocalizationType, .bark)
    }

    func testMockHistoryReturnsNewestFirst() async throws {
        let repository = MockHistoryRepository(latency: 0)
        let analyses = try await repository.fetchAllAnalyses()
        XCTAssertEqual(analyses.count, MockSeeds.demoAnalyses().count)
        let dates = analyses.map(\.createdAt)
        XCTAssertEqual(dates, dates.sorted(by: >))
    }

    func testMockHistoryFiltersByDog() async throws {
        let repository = MockHistoryRepository(latency: 0)
        let maxAnalyses = try await repository.fetchAnalyses(for: MockSeeds.max.id)
        let lunaAnalyses = try await repository.fetchAnalyses(for: MockSeeds.luna.id)
        XCTAssertEqual(maxAnalyses.count, 3)
        XCTAssertEqual(lunaAnalyses.count, 3)
        XCTAssertTrue(maxAnalyses.allSatisfy { $0.dogID == MockSeeds.max.id })
    }

    func testMockHistoryRecordsNewAnalysis() async throws {
        let repository = MockHistoryRepository(seedAnalyses: [], latency: 0)
        let emptyCount = try await repository.fetchAllAnalyses().count
        XCTAssertEqual(emptyCount, 0)
        try await repository.record(MockSeeds.demoAnalyses()[0])
        let countAfterRecord = try await repository.fetchAllAnalyses().count
        XCTAssertEqual(countAfterRecord, 1)
    }

    func testMockInsightsReportsSeededDistribution() async throws {
        let history = MockHistoryRepository(latency: 0)
        let insights = try await MockInsightsRepository(history: history).fetchInsights(for: MockSeeds.max.id)
        XCTAssertEqual(insights.totalAnalyses, 3)
        XCTAssertEqual(insights.stateDistribution.map(\.state).sorted { $0.rawValue < $1.rawValue }, [BehaviorState.attentionSeeking, .calm, .curious])
        XCTAssertEqual(insights.stateDistribution.map(\.count).reduce(0, +), 3)
        XCTAssertEqual(insights.vocalizationDistribution.map(\.count).reduce(0, +), 1)
        XCTAssertEqual(insights.timeOfDayDistribution.map(\.count).reduce(0, +), 3)
    }

    func testMockInsightsEmptyWhenNoAnalyses() async throws {
        let history = MockHistoryRepository(seedAnalyses: [], latency: 0)
        let insights = try await MockInsightsRepository(history: history).fetchInsights(for: MockSeeds.max.id)
        XCTAssertEqual(insights.totalAnalyses, 0)
        XCTAssertTrue(insights.stateDistribution.isEmpty)
        XCTAssertTrue(insights.trendMessage.contains("No analyses yet"))
    }
}