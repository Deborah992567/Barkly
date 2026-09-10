import Foundation

protocol AnalysisRepository: Sendable {
    func requestAnalysis(
        for dogID: UUID,
        inputType: AnalysisInputType,
        vocalizationType: VocalizationType?,
        duration: TimeInterval?
    ) async throws -> BehaviorAnalysis
}