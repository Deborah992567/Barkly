import Foundation

/// Demo/preview insights. Keeps a single source of truth for aggregation by
/// reusing the live `DerivedInsightsRepository`, only resolving dog names from
/// the seed data instead of the app's dog list.
struct MockInsightsRepository: InsightsRepository {
    private let derived: DerivedInsightsRepository

    init(history: any HistoryRepository) {
        self.derived = DerivedInsightsRepository(history: history) { dogID in
            MockSeeds.demoDogs.first { $0.id == dogID }?.name ?? "your dog"
        }
    }

    func fetchInsights(for dogID: UUID) async throws -> InsightsSummary {
        try await derived.fetchInsights(for: dogID)
    }
}