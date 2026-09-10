import Foundation

struct OwnerProfile: Identifiable, Equatable, Hashable, Codable, Sendable {
    let id: UUID
    let name: String
    let email: String
    let memberSince: Date

    init(
        id: UUID = UUID(),
        name: String,
        email: String,
        memberSince: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.email = email
        self.memberSince = memberSince
    }

    var initials: String {
        name
            .split(separator: " ")
            .prefix(2)
            .compactMap { $0.first.map(String.init) }
            .joined()
            .uppercased()
    }
}