import Foundation

enum AppRepositoryError: LocalizedError, Equatable, Sendable {
    case offline
    case serviceUnavailable
    case invalidData
    case permissionDenied
    case unauthorized
    case validation(String)

    var errorDescription: String? {
        switch self {
        case .offline: "You're not connected."
        case .serviceUnavailable: "BARKLY's analysis service isn't available right now."
        case .invalidData: "The media couldn't be read."
        case .permissionDenied: "Access wasn't granted."
        case .unauthorized: "Your session expired. Please sign in again."
        case .validation(let message): message
        }
    }
}

extension AppRepositoryError {
    /// Maps a transport/HTTP error from the API client into a domain-level
    /// failure. 4xx responses that signal bad input carry the server's message
    /// so the UI can tell the owner *what* to fix instead of blaming the network.
    static func from(clientError: APIClientError) -> AppRepositoryError {
        switch clientError {
        case .unauthorized:
            return .unauthorized
        case .http(let status, let message, let code):
            if status == 401 {
                return .unauthorized
            }
            if status == 422 || status == 400 {
                return .validation(message ?? code ?? "This request couldn't be completed.")
            }
            return .serviceUnavailable
        case .transport:
            return .offline
        case .decoding, .invalidRequest:
            return .invalidData
        }
    }
}