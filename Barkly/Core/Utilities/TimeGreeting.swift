import Foundation

enum TimeGreeting {
    static func greeting(for date: Date = Date()) -> String {
        let hour = Calendar.current.component(.hour, from: date)
        switch hour {
        case 5..<12: return "Good morning"
        case 12..<17: return "Good afternoon"
        case 17..<22: return "Good evening"
        default: return "Good evening"
        }
    }
}

enum BarklyDateFormatter {
    static func relative(_ date: Date) -> String {
        date.formatted(.relative(presentation: .named))
    }

    static func dateAndTime(_ date: Date) -> String {
        date.formatted(date: .abbreviated, time: .shortened)
    }

    /// Plain calendar date used on the wire for dog birth dates (the backend
    /// stores `date`, not `datetime`). Uses calendar (local) components so the
    /// date the owner picks is the date that is sent, regardless of timezone.
    static func birthDate(_ date: Date) -> String {
        let components = Calendar.current.dateComponents([.year, .month, .day], from: date)
        guard let year = components.year, let month = components.month, let day = components.day else {
            return ""
        }
        return String(format: "%04d-%02d-%02d", year, month, day)
    }

    /// Parses the backend's `yyyy-MM-dd` birth-date string back into a local
    /// calendar date (midnight), matching what the birth-date picker produces.
    static func parseBirthDate(_ value: String) -> Date? {
        let parts = value.split(separator: "-")
        guard parts.count == 3,
              let year = Int(parts[0]),
              let month = Int(parts[1]),
              let day = Int(parts[2]) else {
            return nil
        }
        return Calendar.current.date(from: DateComponents(year: year, month: month, day: day))
    }
}