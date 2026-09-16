import Foundation
import Observation

enum AuthenticationError: Error, LocalizedError, Equatable {
    case invalidCredentials
    case rateLimitExceeded
    case serviceUnavailable
    case data(String)

    var errorDescription: String? {
        switch self {
        case .invalidCredentials:
            return "The email or password is incorrect."
        case .rateLimitExceeded:
            return "Too many attempts. Please wait a moment and try again."
        case .serviceUnavailable:
            return "BARKLY's servers are unreachable right now."
        case .data(let message):
            return message
        }
    }
}

/// Manages the signed-in session: holds the bearer token, talks to the keychain
/// session store, and exposes a UI-observable authentication state.
@MainActor
@Observable
final class AuthenticationService {
    private let client: APIClient
    private let session: AuthSessionStore

    private(set) var isAuthenticated: Bool
    private(set) var accountEmail: String?
    private(set) var isWorking = false
    private(set) var lastError: String?

    init(client: APIClient, session: AuthSessionStore) {
        self.client = client
        self.session = session
        isAuthenticated = session.isAuthenticated
        accountEmail = session.email
        Task {
            await restore()
        }
    }

    /// Demo mode: treated as already signed in with no backend calls.
    init(demo: Void) {
        client = APIClient(config: .development)
        session = AuthSessionStore(name: "barkly.demo.session")
        isAuthenticated = true
        accountEmail = "demo@barkly.app"
    }

    func restore() async {
        await client.setAuthToken(session.token)
        if session.token != nil {
            isAuthenticated = true
        }
    }

    func login(email: String, password: String) async throws {
        isWorking = true
        lastError = nil
        defer { isWorking = false }
        let request = LoginRequestDTO(email: email, password: password)
        let response: TokenResponseDTO
        do {
            response = try await client.post("api/v1/auth/login", body: request)
        } catch let error as APIClientError {
            throw map(error)
        }
        await persist(response)
    }

    func register(email: String, password: String, displayName: String?) async throws {
        isWorking = true
        lastError = nil
        defer { isWorking = false }
        let request = RegisterRequestDTO(email: email, password: password, displayName: displayName)
        let response: TokenResponseDTO
        do {
            response = try await client.post("api/v1/auth/register", body: request)
        } catch let error as APIClientError {
            throw map(error)
        }
        await persist(response)
    }

    func signOut() async {
        session.clear()
        await client.setAuthToken(nil)
        isAuthenticated = false
        accountEmail = nil
    }

    private func persist(_ response: TokenResponseDTO) async {
        await client.setAuthToken(response.accessToken)
        session.save(token: response.accessToken, email: response.user.email)
        isAuthenticated = true
        accountEmail = response.user.email
    }

    private func map(_ error: APIClientError) -> Error {
        switch error {
        case .http(let status, let message, _):
            switch status {
            case 401, 400:
                return AuthenticationError.invalidCredentials
            case 429:
                return AuthenticationError.rateLimitExceeded
            case 502, 503:
                return AuthenticationError.serviceUnavailable
            default:
                return AuthenticationError.data(message)
            }
        case .transport:
            return AuthenticationError.serviceUnavailable
        case .decoding, .unauthorized, .invalidRequest:
            return AuthenticationError.data(String(describing: error))
        }
    }
}

// MARK: - Request DTOs

struct LoginRequestDTO: Encodable, Sendable {
    let email: String
    let password: String
}

struct RegisterRequestDTO: Encodable, Sendable {
    let email: String
    let password: String
    let displayName: String?
}