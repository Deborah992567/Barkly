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
    /// BARKLY does not call something a pattern until it has this many usable
    /// (completed) interpretations for the dog.
    static let minimumAnalysesForPatterns = 3

    let dogID: UUID
    let totalAnalyses: Int
    let mostCommonVocalization: VocalizationType?
    let mostFrequentState: BehaviorState?
    let mostActiveTime: TimeOfDay?
    let trendMessage: String
    let stateDistribution: [StateStat]
    let timeOfDayDistribution: [TimeOfDayStat]
    let vocalizationDistribution: [VocalizationStat]
    /// How many completed interpretations back these numbers.
    let usableAnalyses: Int
    /// True when there are too few usable interpretations to describe a pattern.
    let isInsufficientData: Bool

    init(
        dogID: UUID,
        totalAnalyses: Int,
        mostCommonVocalization: VocalizationType?,
        mostFrequentState: BehaviorState?,
        mostActiveTime: TimeOfDay?,
        trendMessage: String,
        stateDistribution: [StateStat],
        timeOfDayDistribution: [TimeOfDayStat],
        vocalizationDistribution: [VocalizationStat],
        usableAnalyses: Int = 0,
        isInsufficientData: Bool = false
    ) {
        self.dogID = dogID
        self.totalAnalyses = totalAnalyses
        self.mostCommonVocalization = mostCommonVocalization
        self.mostFrequentState = mostFrequentState
        self.mostActiveTime = mostActiveTime
        self.trendMessage = trendMessage
        self.stateDistribution = stateDistribution
        self.timeOfDayDistribution = timeOfDayDistribution
        self.vocalizationDistribution = vocalizationDistribution
        self.usableAnalyses = usableAnalyses
        self.isInsufficientData = isInsufficientData
    }
}