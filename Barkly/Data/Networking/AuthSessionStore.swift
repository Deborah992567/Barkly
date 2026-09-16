import Foundation
import Security

/// Keychain-backed storage for the API bearer token and account email.
/// Lock-protected so it can be read synchronously by the UI layer.
final class AuthSessionStore: Sendable {
    private let lock = NSLock()
    private let service: String
    private let tokenKey = "barkly.accessToken"
    private let emailKey = "barkly.accountEmail"

    private var storedToken: String?
    private var storedEmail: String?

    init(name: String = "com.barkly.app.session") {
        service = name
        storedToken = Self.read(service: service, account: tokenKey)
        storedEmail = Self.read(service: service, account: emailKey)
    }

    var token: String? {
        lock.lock()
        defer { lock.unlock() }
        return storedToken
    }

    var email: String? {
        lock.lock()
        defer { lock.unlock() }
        return storedEmail
    }

    var isAuthenticated: Bool {
        token != nil
    }

    func save(token: String, email: String) {
        lock.lock()
        storedToken = token
        storedEmail = email
        lock.unlock()
        Self.write(token, service: service, account: tokenKey)
        Self.write(email, service: service, account: emailKey)
    }

    func clear() {
        lock.lock()
        storedToken = nil
        storedEmail = nil
        lock.unlock()
        Self.delete(service: service, account: tokenKey)
        Self.delete(service: service, account: emailKey)
    }

    // MARK: Keychain helpers

    private static func read(service: String, account: String) -> String? {
        var query = baseQuery(service: service, account: account)
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne

        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let data = item as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    private static func write(_ value: String, service: String, account: String) {
        let data = Data(value.utf8)
        var query = baseQuery(service: service, account: account)
        let attributes: [String: Any] = [kSecValueData as String: data]

        let status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if status == errSecItemNotFound {
            query[kSecValueData as String] = data
            SecItemAdd(query as CFDictionary, nil)
        }
    }

    private static func delete(service: String, account: String) {
        SecItemDelete(baseQuery(service: service, account: account) as CFDictionary)
    }

    private static func baseQuery(service: String, account: String) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
    }
}