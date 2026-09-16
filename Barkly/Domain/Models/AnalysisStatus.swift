import Foundation

/// The backend analysis lifecycle. Mirrors the API status values exactly so a
/// completed-with-UNKNOWN result is never confused with a failed analysis.
enum AnalysisStatus: String, Codable, CaseIterable, Sendable {
    case created = "CREATED"
    case queued = "QUEUED"
    case processing = "PROCESSING"
    case completed = "COMPLETED"
    case failed = "FAILED"
    case cancelled = "CANCELLED"

    init(apiValue: String) {
        self = AnalysisStatus(rawValue: apiValue) ?? .failed
    }

    var isTerminal: Bool {
        self == .completed || self == .failed || self == .cancelled
    }

    var isInProgress: Bool {
        self == .created || self == .queued || self == .processing
    }

    var isSuccessful: Bool {
        self == .completed
    }

    /// Used by the UI to decide whether a result page can be shown.
    var isUsableResult: Bool {
        self == .completed
    }
}