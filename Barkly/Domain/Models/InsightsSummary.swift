import Foundation

struct StateStat: Identifiable, Hashable, Codable, Sendable {
    var id: BehaviorState { state }
    let state: BehaviorState
    let count: Int
}

struct TimeOfDayStat: Identifiable, Hashable, Codable, Sendable {
    var id: TimeOfDay { bucket }
    let bucket: TimeOfDay
    let count: Int
}

struct VocalizationStat: Identifiable, Hashable, Codable, Sendable {
    var id: VocalizationType { type }
    let type: VocalizationType
    let count: Int
}

enum TimeOfDay: String, Codable, CaseIterable, Sendable {
    case morning
    case afternoon
    case evening
    case night

    var displayName: String {
        switch self {
        case .morning: "Morning"
        case .afternoon: "Afternoon"
        case .evening: "Evening"
        case .night: "Night"
        }
    }
}

struct InsightsSummary: Equatable, Hashable, Codable, Sendable {
    let dogID: UUID
    let totalAnalyses: Int
    let mostCommonVocalization: VocalizationType?
    let mostFrequentState: BehaviorState?
    let mostActiveTime: TimeOfDay?
    let trendMessage: String
    let stateDistribution: [StateStat]
    let timeOfDayDistribution: [TimeOfDayStat]
    let vocalizationDistribution: [VocalizationStat]
}