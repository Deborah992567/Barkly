import Foundation

protocol HistoryRepository: Sendable {
    func fetchAllAnalyses() async throws -> [BehaviorAnalysis]
    func fetchAnalyses(for dogID: UUID) async throws -> [BehaviorAnalysis]
    func record(_ analysis: BehaviorAnalysis) async throws
}