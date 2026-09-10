import Foundation

protocol InsightsRepository: Sendable {
    func fetchInsights(for dogID: UUID) async throws -> InsightsSummary
}