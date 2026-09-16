import Foundation

// MARK: - Domain mapping helpers

extension Dog {
    init(dto: DogDTO) {
        self.init(
            id: dto.id,
            name: dto.name,
            breed: dto.breed ?? "",
            dateOfBirth: dto.dateOfBirth ?? Date(),
            notes: dto.notes
        )
    }
}

extension BehaviorState {
    /// Maps a backend `primary_behavior` to the app's state, keeping any
    /// backend-only emotional labels out of the primary headline.
    static func fromPrimaryBehavior(_ raw: String) -> BehaviorState {
        BehaviorState(apiValue: raw)
    }
}

extension BehaviorAnalysis {
    init(dto: AnalysisDTO) {
        let result = dto.result
        let secondary = result?.secondaryBehaviors.map(BehaviorState.init(apiValue:)) ?? []
        self.init(
            id: dto.analysisId,
            dogID: dto.dogId,
            createdAt: dto.createdAt,
            inputType: AnalysisInputType(apiValue: dto.inputType) ?? .behavior,
            estimatedState: result.map { BehaviorState.fromPrimaryBehavior($0.primaryBehavior) } ?? .unknown,
            confidence: result.map { Float($0.confidence) } ?? 0,
            observations: result?.observations.map(\.description) ?? [],
            explanation: result?.explanation ?? "No explanation was returned for this analysis.",
            secondaryBehaviors: secondary,
            safetyNote: dto.result?.disclaimer,
            modelName: result?.modelName,
            modelVersion: result?.modelVersion,
            isInsufficientEvidence: result?.isInsufficientEvidence ?? false
        )
    }
}

extension HistoryPage {
    init(dto: HistoryPageDTO) {
        self.init(
            items: dto.items.map(BehaviorAnalysis.init(dto:)),
            page: dto.page,
            pageSize: dto.pageSize,
            total: dto.total,
            hasNext: dto.hasNext
        )
    }
}

// MARK: - Wire mapping helpers

func apiDurationMillis(_ duration: TimeInterval?) -> Int? {
    guard let duration, duration > 0 else { return nil }
    return Int((duration * 1000).rounded())
}

func apiContext(_ context: AnalysisContextInput?) -> AnalysisContextInputDTO? {
    guard let context else { return nil }
    let hasContent = context.ownerPresence != nil
        || context.activityState != nil
        || context.recentFeeding != nil
        || context.recentWalk != nil
        || context.recentPlay != nil
        || context.presenceOfStrangers != nil
        || context.presenceOfOtherAnimals != nil
        || context.recentStressfulEvent != nil
        || context.locationCategory != nil
    guard hasContent else { return nil }
    return AnalysisContextInputDTO(
        ownerPresence: context.ownerPresence?.rawValue,
        activityState: context.activityState?.rawValue,
        timeOfDay: nil,
        recentFeeding: context.recentFeeding,
        recentWalk: context.recentWalk,
        recentPlay: context.recentPlay,
        presenceOfStrangers: context.presenceOfStrangers,
        presenceOfOtherAnimals: context.presenceOfOtherAnimals,
        recentStressfulEvent: context.recentStressfulEvent,
        locationCategory: context.locationCategory
    )
}