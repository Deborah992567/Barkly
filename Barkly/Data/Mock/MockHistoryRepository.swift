import Foundation

final class MockHistoryRepository: HistoryRepository {
    private let store: InMemoryAnalysisStore
    private let latency: UInt64

    init(seedAnalyses: [BehaviorAnalysis] = MockSeeds.demoAnalyses(), latency: UInt64 = 180_000_000) {
        self.latency = latency
        store = InMemoryAnalysisStore(items: seedAnalyses)
    }

    func fetchAllAnalyses() async throws -> [BehaviorAnalysis] {
        if latency > 0 {
            try await Task.sleep(nanoseconds: latency)
        }
        return await store.all()
    }

    func fetchAnalyses(for dogID: UUID) async throws -> [BehaviorAnalysis] {
        try await fetchAllAnalyses().filter { $0.dogID == dogID }
    }

    func record(_ analysis: BehaviorAnalysis) async throws {
        await store.append(analysis)
    }
}

actor InMemoryAnalysisStore {
    private var items: [BehaviorAnalysis]

    init(items: [BehaviorAnalysis]) {
        self.items = items
    }

    func all() -> [BehaviorAnalysis] {
        items.sorted { $0.createdAt > $1.createdAt }
    }

    func append(_ analysis: BehaviorAnalysis) {
        items.append(analysis)
    }
}