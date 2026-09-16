import Foundation

/// Whether the owner is present during the captured moment. Mirrors the
/// backend `OwnerPresence` enum.
enum OwnerPresence: String, CaseIterable, Sendable {
    case home = "HOME"
    case away = "AWAY"
    case unknown = "UNKNOWN"

    var displayName: String {
        switch self {
        case .home: "Home with me"
        case .away: "I'm away"
        case .unknown: "Not sure"
        }
    }
}

/// What the dog was doing when the moment was captured. Mirrors the backend
/// `ActivityState` enum.
enum ActivityState: String, CaseIterable, Sendable {
    case resting = "RESTING"
    case walking = "WALKING"
    case playing = "PLAYING"
    case eating = "EATING"
    case training = "TRAINING"
    case unknown = "UNKNOWN"

    var displayName: String {
        switch self {
        case .resting: "Resting or sleeping"
        case .walking: "On a walk"
        case .playing: "Playing"
        case .eating: "Eating"
        case .training: "Training"
        case .unknown: "Other"
        }
    }
}

/// Optional answers to the context questions captured around an analysis.
/// Every field is optional — the backend never forces an answer.
struct AnalysisContextInput: Equatable, Sendable {
    var ownerPresence: OwnerPresence?
    var activityState: ActivityState?
    var recentFeeding: Bool?
    var recentWalk: Bool?
    var recentPlay: Bool?
    var presenceOfStrangers: Bool?
    var presenceOfOtherAnimals: Bool?
    var recentStressfulEvent: Bool?
    var locationCategory: String?

    static var empty: AnalysisContextInput {
        AnalysisContextInput()
    }
}