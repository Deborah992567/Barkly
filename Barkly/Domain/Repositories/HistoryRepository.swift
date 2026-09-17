import Foundation

protocol HistoryRepository: Sendable {
    func fetchAllAnalyses() async throws -> [BehaviorAnalysis]
    func fetchAnalyses(for dogID: UUID) async throws -> [BehaviorAnalysis]
    func record(_ analysis: BehaviorAnalysis) async throws
    func fetchHistoryPage(
        dogID: UUID?,
        behavior: BehaviorState?,
        page: Int,
        pageSize: Int?
    ) async throws -> HistoryPage
}