import Foundation

final class MockInsightsRepository: InsightsRepository {
    private let history: any HistoryRepository

    init(history: any HistoryRepository) {
        self.history = history
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

        let stateDistribution = Self.distribution(
            of: analyses.compactMap { $0.estimatedState.rawValue },
            all: BehaviorState.allCases.map(\.rawValue)
        )
        .map { StateStat(state: BehaviorState(rawValue: $0.key) ?? .unknown, count: $0.value) }
        .filter { $0.count > 0 }
        .sorted { $0.count > $1.count }

        let timeBuckets = analyses.map { Self.timeOfDay(for: $0.createdAt) }
        let timeOfDayDistribution = TimeOfDay.allCases
            .map { bucket in
                let count = timeBuckets.filter { $0 == bucket }.count
                return TimeOfDayStat(bucket: bucket, count: count)
            }
            .filter { $0.count > 0 }
            .sorted { $0.count > $1.count }

        let vocalizations = analyses.compactMap { $0.vocalizationType }
        let vocalizationDistribution = VocalizationType.allCases
            .map { type in
                let count = vocalizations.filter { $0 == type }.count
                return VocalizationStat(type: type, count: count)
            }
            .filter { $0.count > 0 }
            .sorted { $0.count > $1.count }

        let dog = MockSeeds.demoDogs.first(where: { $0.id == dogID })
        let mostFrequentState = stateDistribution.first?.state
        let mostCommonVocalization = vocalizationDistribution.first?.type
        let mostActiveTime = timeOfDayDistribution.first?.bucket

        let trendMessage = Self.trendMessage(
            dogName: dog?.name ?? "your dog",
            mostFrequentState: mostFrequentState,
            mostCommonVocalization: mostCommonVocalization,
            mostActiveTime: mostActiveTime,
            analyses: analyses
        )

        return InsightsSummary(
            dogID: dogID,
            totalAnalyses: analyses.count,
            mostCommonVocalization: mostCommonVocalization,
            mostFrequentState: mostFrequentState,
            mostActiveTime: mostActiveTime,
            trendMessage: trendMessage,
            stateDistribution: stateDistribution,
            timeOfDayDistribution: timeOfDayDistribution,
            vocalizationDistribution: vocalizationDistribution
        )
    }

    private static func distribution(of values: [String], all: [String]) -> [String: Int] {
        var counts: [String: Int] = [:]
        all.forEach { counts[$0, default: 0] += 0 }
        values.forEach { counts[$0, default: 0] += 1 }
        return counts
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
        mostActiveTime: TimeOfDay?,
        analyses: [BehaviorAnalysis]
    ) -> String {
        guard let state = mostFrequentState, let vocalization = mostCommonVocalization, let time = mostActiveTime else {
            return "Keep capturing moments with \(dogName) and BARKLY will start to spot patterns."
        }
        return "\(dogName) shows \(state.shortName.lowercased()) most often, especially \(vocalization.displayName.lowercased())s during the \(time.displayName.lowercased()). \(dogName) gets voiceful when left alone more than before — a pattern worth watching."
    }
}