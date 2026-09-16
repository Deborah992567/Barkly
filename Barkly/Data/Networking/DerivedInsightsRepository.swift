import Foundation

/// Aggregates real analysis history into the insights dashboard, replacing the
/// seed-only mock when the app talks to the backend.
struct DerivedInsightsRepository: InsightsRepository {
    private let history: any HistoryRepository
    private let dogName: @Sendable (UUID) -> String

    init(history: any HistoryRepository, dogName: @escaping @Sendable (UUID) -> String = { _ in "your dog" }) {
        self.history = history
        self.dogName = dogName
    }

    func fetchInsights(for dogID: UUID) async throws -> InsightsSummary {
        let analyses = try await history.fetchAnalyses(for: dogID)
        guard !analyses.isEmpty else {
            return InsightsSummary(
                dogID: dogID,
                totalAnalyses: 0,
                mostCommonVocalization: nil,
                mostFrequentState: nil,
                mostActiveTime: nil,
                trendMessage: "No analyses yet. BARKLY's patterns will appear here after you capture a few moments with your dog.",
                stateDistribution: [],
                timeOfDayDistribution: [],
                vocalizationDistribution: []
            )
        }

        let stateDistribution = analyses
            .reduce(into: [BehaviorState: Int]()) { $0[$1.estimatedState, default: 0] += 1 }
            .map { StateStat(state: $0.key, count: $0.value) }
            .filter { $0.count > 0 }
            .sorted { $0.count > $1.count }

        let timeOfDayDistribution = TimeOfDay.allCases
            .map { bucket in
                TimeOfDayStat(bucket: bucket, count: analyses.filter { Self.timeOfDay(for: $0.createdAt) == bucket }.count)
            }
            .filter { $0.count > 0 }
            .sorted { $0.count > $1.count }

        let vocalizationDistribution = VocalizationType.allCases
            .map { type in
                VocalizationStat(type: type, count: analyses.filter { $0.vocalizationType == type }.count)
            }
            .filter { $0.count > 0 }
            .sorted { $0.count > $1.count }

        let mostFrequentState = stateDistribution.first?.state
        let mostCommonVocalization = vocalizationDistribution.first?.type
        let mostActiveTime = timeOfDayDistribution.first?.bucket

        return InsightsSummary(
            dogID: dogID,
            totalAnalyses: analyses.count,
            mostCommonVocalization: mostCommonVocalization,
            mostFrequentState: mostFrequentState,
            mostActiveTime: mostActiveTime,
            trendMessage: Self.trendMessage(
                dogName: dogName(dogID),
                mostFrequentState: mostFrequentState,
                mostCommonVocalization: mostCommonVocalization,
                mostActiveTime: mostActiveTime
            ),
            stateDistribution: stateDistribution,
            timeOfDayDistribution: timeOfDayDistribution,
            vocalizationDistribution: vocalizationDistribution
        )
    }

    private static func timeOfDay(for date: Date) -> TimeOfDay {
        let hour = Calendar.current.component(.hour, from: date)
        switch hour {
        case 5..<12: return .morning
        case 12..<17: return .afternoon
        case 17..<22: return .evening
        default: return .night
        }
    }

    private static func trendMessage(
        dogName: String,
        mostFrequentState: BehaviorState?,
        mostCommonVocalization: VocalizationType?,
        mostActiveTime: TimeOfDay?
    ) -> String {
        guard let state = mostFrequentState, let time = mostActiveTime else {
            return "Keep capturing moments with \(dogName) and BARKLY will start to spot patterns."
        }
        var message = "\(dogName) most often shows \(state.shortName.lowercased()), especially during the \(time.displayName.lowercased())."
        if let vocalization = mostCommonVocalization {
            message += " \(vocalization.displayName.capitalized)s are the most common vocalization captured so far."
        }
        return message
    }
}