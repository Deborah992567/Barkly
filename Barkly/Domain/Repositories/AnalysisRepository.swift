import Foundation

protocol AnalysisRepository: Sendable {
    /// Legacy entry point: runs an analysis for a captured moment.
    func requestAnalysis(
        for dogID: UUID,
        inputType: AnalysisInputType,
        vocalizationType: VocalizationType?,
        duration: TimeInterval?
    ) async throws -> BehaviorAnalysis

    /// Runs an analysis that needs media captured on-device (audio/video/photo).
    /// `mediaURLs` are local files that will be uploaded before the analysis runs.
    func requestAnalysis(
        for dogID: UUID,
        inputType: AnalysisInputType,
        mediaURLs: [URL],
        duration: TimeInterval?,
        context: AnalysisContextInput?
    ) async throws -> BehaviorAnalysis

    /// Runs a pure behavior-observation analysis (no media).
    func requestBehaviorAnalysis(
        for dogID: UUID,
        context: AnalysisContextInput?
    ) async throws -> BehaviorAnalysis
}

extension AnalysisRepository {
    func requestAnalysis(
        for dogID: UUID,
        inputType: AnalysisInputType,
        mediaURLs: [URL],
        duration: TimeInterval?,
        context: AnalysisContextInput?
    ) async throws -> BehaviorAnalysis {
        try await requestAnalysis(
            for: dogID,
            inputType: inputType,
            vocalizationType: Self.vocalization(for: inputType),
            duration: duration
        )
    }

    func requestBehaviorAnalysis(
        for dogID: UUID,
        context: AnalysisContextInput?
    ) async throws -> BehaviorAnalysis {
        try await requestAnalysis(
            for: dogID,
            inputType: .behavior,
            vocalizationType: nil,
            duration: nil
        )
    }

    private static func vocalization(for inputType: AnalysisInputType) -> VocalizationType? {
        switch inputType {
        case .audio: .bark
        case .video, .photo, .behavior: nil
        }
    }
}