import Foundation

enum APIClientError: Error, Equatable, Sendable {
    case transport(String)
    case http(Int, String, String?)
    case decoding(String)
    case unauthorized
    case invalidRequest
}

struct APIConfig: Sendable {
    let baseURL: URL
    let timeout: TimeInterval

    static var development: APIConfig {
        let env = ProcessInfo.processInfo.environment
        let raw = env["BARKLY_API_BASE_URL"] ?? "http://127.0.0.1:8000"
        return APIConfig(baseURL: URL(string: raw) ?? URL(string: "http://127.0.0.1:8000")!, timeout: 60)
    }
}

/// Minimal HTTP client for BARKLY's API.
///
/// All JSON bodies use snake_case (as the backend expects) and responses are
/// decoded with `.convertFromSnakeCase`. The bearer token is injected by the
/// session store; a 401 surfaces as `.unauthorized` so the auth layer can react.
actor APIClient: Sendable {
    private let config: APIConfig
    private let session: URLSession
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder
    private(set) var authToken: String?

    init(config: APIConfig, session: URLSession = .shared) {
        self.config = config
        self.session = session
        encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .iso8601
        decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .iso8601
    }

    func setAuthToken(_ token: String?) {
        authToken = token
    }

    func token() -> String? {
        authToken
    }

    // MARK: Verbs

    func get<Response: Decodable & Sendable>(
        _ path: String,
        query: [URLQueryItem] = []
    ) async throws -> Response {
        var request = try makeRequest(path: path, query: query, method: "GET")
        return try await send(&request)
    }

    func post<Body: Encodable & Sendable, Response: Decodable & Sendable>(
        _ path: String,
        body: Body
    ) async throws -> Response {
        var request = try makeRequest(path: path, method: "POST")
        request.httpBody = try encoder.encode(body)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        return try await send(&request)
    }

    func post<Response: Decodable & Sendable>(_ path: String) async throws -> Response {
        var request = try makeRequest(path: path, method: "POST")
        return try await send(&request)
    }

    func patch<Body: Encodable & Sendable, Response: Decodable & Sendable>(
        _ path: String,
        body: Body
    ) async throws -> Response {
        var request = try makeRequest(path: path, method: "PATCH")
        request.httpBody = try encoder.encode(body)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        return try await send(&request)
    }

    func delete(_ path: String) async throws {
        var request = try makeRequest(path: path, method: "DELETE")
        _ = try await sendData(&request)
    }

    /// Multipart uploads a file (used for media assets).
    @discardableResult
    func upload(
        _ path: String,
        fileData: Data,
        filename: String,
        mimeType: String,
        form: [(String, String)]
    ) async throws -> Data {
        var request = try makeRequest(path: path, method: "POST")
        let boundary = "Barkly-\(UUID().uuidString)"
        request.setValue(
            "multipart/form-data; boundary=\(boundary)",
            forHTTPHeaderField: "Content-Type"
        )

        var body = Data()
        for (key, value) in form {
            body.appendString("--\(boundary)\r\n")
            body.appendString("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n")
            body.appendString("\(value)\r\n")
        }
        body.appendString("--\(boundary)\r\n")
        body.appendString("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n")
        body.appendString("Content-Type: \(mimeType)\r\n\r\n")
        body.append(fileData)
        body.appendString("\r\n--\(boundary)--\r\n")
        request.httpBody = body

        return try await sendData(&request)
    }

    // MARK: Plumbing

    private func makeRequest(path: String, query: [URLQueryItem] = [], method: String) throws -> URLRequest {
        guard var components = URLComponents(url: config.baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false) else {
            throw APIClientError.invalidRequest
        }
        if !query.isEmpty {
            components.queryItems = query
        }
        guard let url = components.url else {
            throw APIClientError.invalidRequest
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = config.timeout
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue(UUID().uuidString, forHTTPHeaderField: "X-Request-Id")
        if let authToken {
            request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        return request
    }

    private func send<Response: Decodable & Sendable>(_ request: inout URLRequest) async throws -> Response {
        let data = try await sendData(&request)
        do {
            return try decoder.decode(Response.self, from: data)
        } catch {
            throw APIClientError.decoding(String(describing: error))
        }
    }

    private func sendData(_ request: inout URLRequest) async throws -> Data {
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIClientError.transport(String(describing: error))
        }
        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.transport("No HTTP response")
        }
        guard (200..<300).contains(http.statusCode) else {
            if http.statusCode == 401 {
                authToken = nil
                throw APIClientError.unauthorized
            }
            let message = Self.errorMessage(from: data)
            throw APIClientError.http(http.statusCode, message ?? "Request failed", codeFor(http.statusCode))
        }
        return data
    }

    private func codeFor(_ status: Int) -> String? {
        guard status >= 400 else { return nil }
        return status == 409 ? "CONFLICT" : (status == 422 ? "VALIDATION" : "SERVER")
    }

    private static func errorMessage(from data: Data) -> String? {
        guard let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return nil
        }
        if let message = object["message"] as? String {
            return message
        }
        if let error = object["error"] as? [String: Any] {
            if let message = error["message"] as? String {
                return message
            }
            if let code = error["code"] as? String {
                return code
            }
        }
        if let detail = object["detail"] as? String {
            return detail
        }
        if let detail = object["detail"] as? [[String: Any]],
           let first = detail.first,
           let message = first["msg"] as? String {
            return message
        }
        return nil
    }
}

private extension Data {
    mutating func appendString(_ value: String) {
        append(Data(value.utf8))
    }
}