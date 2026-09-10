import Foundation

struct Dog: Identifiable, Hashable, Codable, Sendable {
    let id: UUID
    var name: String
    var breed: String
    var dateOfBirth: Date
    var notes: String?

    init(
        id: UUID = UUID(),
        name: String,
        breed: String,
        dateOfBirth: Date,
        notes: String? = nil
    ) {
        self.id = id
        self.name = name
        self.breed = breed
        self.dateOfBirth = dateOfBirth
        self.notes = notes
    }

    var ageInYears: Int {
        Calendar.current.dateComponents([.year], from: dateOfBirth, to: Date()).year ?? 0
    }

    var ageDescription: String {
        let years = ageInYears
        if years <= 0 {
            let months = Calendar.current.dateComponents([.month], from: dateOfBirth, to: Date()).month ?? 0
            return "\(max(months, 1)) month\(months == 1 ? "" : "s") old"
        }
        return "\(years) year\(years == 1 ? "" : "s") old"
    }
}