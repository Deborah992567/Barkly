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
}