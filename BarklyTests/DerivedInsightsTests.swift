import XCTest
@testable import Barkly

final class DerivedInsightsTests: XCTestCase {

    func testNoAnalysesReportsNoData() async throws {
        let repo = DerivedInsightsRepository(history: MockHistoryRepository(seedAnalyses: []))
        let insights = try await repo.fetchInsights(for: MockSeeds.max.id)

        XCTAssertEqual(insights.totalAnalyses, 0)
        XCTAssertEqual(insights.usableAnalyses, 0)
        XCTAssertTrue(insights.isInsufficientData)
        XCTAssertTrue(insights.stateDistribution.isEmpty)
        XCTAssertTrue(insights.trendMessage.contains("No analyses yet"))
    }

    func testInFlightAndFailedAnalysesDoNotCountTowardPatterns() async throws {
        let seeds = [
            analysis(status: .processing, state: .excited),
            analysis(status: .failed, state: .fearful),
            analysis(status: .cancelled, state: .calm)
        ]
        let repo = DerivedInsightsRepository(history: MockHistoryRepository(seedAnalyses: seeds))

        let insights = try await repo.fetchInsights(for: MockSeeds.max.id)

        XCTAssertEqual(insights.totalAnalyses, 3)
        XCTAssertEqual(insights.usableAnalyses, 0)
        XCTAssertTrue(insights.isInsufficientData)
        XCTAssertTrue(insights.stateDistribution.isEmpty)
        XCTAssertNil(insights.mostFrequentState)
        XCTAssertTrue(insights.trendMessage.contains("No finished interpretations yet"))
    }

    func testFewerThanThreeUsableAnalysesIsInsufficient() async throws {
        let seeds = [
            analysis(status: .completed, state: .calm),
            analysis(status: .completed, state: .calm),
            analysis(status: .processing, state: .excited)
        ]
        let repo = DerivedInsightsRepository(history: MockHistoryRepository(seedAnalyses: seeds))

        let insights = try await repo.fetchInsights(for: MockSeeds.max.id)

        XCTAssertEqual(insights.usableAnalyses, 2)
        XCTAssertTrue(insights.isInsufficientData)
        XCTAssertEqual(insights.stateDistribution, [StateStat(state: .calm, count: 2)])
        XCTAssertTrue(insights.trendMessage.contains("2 of 3"))
        XCTAssertFalse(insights.trendMessage.contains("most often"))
    }

    func testThreeUsableAnalysesEnablePatternDescription() async throws {
        let seeds = [
            analysis(status: .completed, state: .calm),
            analysis(status: .completed, state: .calm),
            analysis(status: .completed, state: .playful),
            analysis(status: .failed, state: .fearful)
        ]
        let repo = DerivedInsightsRepository(history: MockHistoryRepository(seedAnalyses: seeds))

        let insights = try await repo.fetchInsights(for: MockSeeds.max.id)

        XCTAssertEqual(insights.usableAnalyses, 3)
        XCTAssertFalse(insights.isInsufficientData)
        XCTAssertEqual(insights.mostFrequentState, .calm)
        XCTAssertEqual(insights.stateDistribution, [
            StateStat(state: .calm, count: 2),
            StateStat(state: .playful, count: 1)
        ])
        XCTAssertTrue(insights.trendMessage.contains("Across 3 interpretations so far"))
        XCTAssertTrue(insights.trendMessage.contains("most often shown calm"))
        XCTAssertTrue(insights.trendMessage.contains("not a diagnosis"))
    }

    func testVocalizationDistributionUsesOnlyCompleted() async throws {
        let seeds = [
            analysis(status: .completed, state: .calm, vocalization: .bark),
            analysis(status: .completed, state: .playful, vocalization: .bark),
            analysis(status: .completed, state: .playful, vocalization: .whine),
            analysis(status: .processing, state: .excited, vocalization: .growl)
        ]
        let repo = DerivedInsightsRepository(history: MockHistoryRepository(seedAnalyses: seeds))

        let insights = try await repo.fetchInsights(for: MockSeeds.max.id)

        XCTAssertEqual(insights.mostCommonVocalization, .bark)
        XCTAssertEqual(insights.vocalizationDistribution, [
            VocalizationStat(type: .bark, count: 2),
            VocalizationStat(type: .whine, count: 1)
        ])
    }

    func testSumOfStateCountsMatchesUsableAnalyses() async throws {
        let seeds = [
            analysis(status: .completed, state: .calm),
            analysis(status: .completed, state: .calm),
            analysis(status: .completed, state: .calm),
            analysis(status: .completed, state: .anxious),
            analysis(status: .completed, state: .excited),
            analysis(status: .failed, state: .fearful)
        ]
        let repo = DerivedInsightsRepository(history: MockHistoryRepository(seedAnalyses: seeds))

        let insights = try await repo.fetchInsights(for: MockSeeds.max.id)

        XCTAssertEqual(insights.stateDistribution.map(\.count).reduce(0, +), 5)
        XCTAssertEqual(insights.totalAnalyses, 6)
        XCTAssertFalse(insights.isInsufficientData)
    }

    private func analysis(
        status: AnalysisStatus,
        state: BehaviorState,
        vocalization: VocalizationType? = nil
    ) -> BehaviorAnalysis {
        BehaviorAnalysis(
            dogID: MockSeeds.max.id,
            createdAt: Date(timeIntervalSince1970: 1_600_000_000),
            inputType: .audio,
            status: status,
            failureMessage: status == .failed ? "Analysis failed" : nil,
            vocalizationType: vocalization,
            estimatedState: state,
            confidence: 0.7,
            observations: ["Observation"],
            explanation: "Explanation"
        )
    }
}