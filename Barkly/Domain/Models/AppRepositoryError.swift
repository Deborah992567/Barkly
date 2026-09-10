import Foundation

enum AppRepositoryError: LocalizedError, Equatable, Sendable {
    case offline
    case serviceUnavailable
    case invalidData
    case permissionDenied

    var errorDescription: String? {
        switch self {
        case .offline: "You're not connected."
        case .serviceUnavailable: "BARKLY's analysis service isn't available right now."
        case .invalidData: "The media couldn't be read."
        case .permissionDenied: "Access wasn't granted."
        }
    }
}