import Foundation

enum VocalizationType: String, Codable, CaseIterable, Sendable {
    case bark
    case whine
    case growl
    case howl
    case grumble
    case silence

    var displayName: String {
        switch self {
        case .bark: "Bark"
        case .whine: "Whine"
        case .growl: "Growl"
        case .howl: "Howl"
        case .grumble: "Grumble"
        case .silence: "Silence"
        }
    }
}