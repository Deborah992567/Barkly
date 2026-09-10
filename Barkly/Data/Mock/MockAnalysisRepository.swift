import Foundation

struct MockAnalysisRepository: AnalysisRepository {
    let latency: UInt64

    init(latency: UInt64 = 280_000_000) {
        self.latency = latency
    }

    func requestAnalysis(
        for dogID: UUID,
        inputType: AnalysisInputType,
        vocalizationType: VocalizationType?,
        duration: TimeInterval?
    ) async throws -> BehaviorAnalysis {
        if latency > 0 {
            try await Task.sleep(nanoseconds: latency)
        }

        let (state, confidence, observations) = Self.demoResult(for: inputType)
        let dogName = MockSeeds.demoDogs.first(where: { $0.id == dogID })?.name ?? "your dog"

        return BehaviorAnalysis(
            dogID: dogID,
            inputType: inputType,
            vocalizationType: vocalizationType ?? Self.defaultVocalization(for: inputType),
            estimatedState: state,
            confidence: confidence,
            observations: observations,
            explanation: Self.explanation(for: state, dogName: dogName, inputType: inputType)
        )
    }

    private static func defaultVocalization(for inputType: AnalysisInputType) -> VocalizationType? {
        switch inputType {
        case .audio: .bark
        case .video, .photo, .behavior: nil
        }
    }

    static func demoResult(for inputType: AnalysisInputType) -> (BehaviorState, Float, [String]) {
        switch inputType {
        case .audio:
            (.attentionSeeking, 0.82, [
                "Repeated vocalization",
                "Short intervals between sounds",
                "Alert posture",
                "Movement toward owner"
            ])
        case .video:
            (.playful, 0.78, [
                "Loose, wiggly body",
                "Play bow observed",
                "Tail wagging broadly",
                "Quick orientation shifts"
            ])
        case .photo:
            (.calm, 0.74, [
                "Relaxed posture",
                "Soft eye contact",
                "Neutral tail position",
                "Slow breathing"
            ])
        case .behavior:
            (.curious, 0.71, [
                "Head tilt",
                "Ears forward",
                "Sniffing intently",
                "Focused attention"
            ])
        }
    }

    private static func explanation(
        for state: BehaviorState,
        dogName: String,
        inputType: AnalysisInputType
    ) -> String {
        let base: String
        switch state {
        case .attentionSeeking:
            base = "The sounds arrived in short, regular bursts while \(dogName) faced your direction. Regular timing plus forward attention most often means your dog is trying to start an interaction."
        case .playful:
            base = "A loose, wiggly frame with quick, bouncy movement is one of the clearest signals for play. \(dogName) looks ready for a fun exchange rather than conflict."
        case .calm:
            base = "Every visible signal is low energy: a settled frame, soft gaze, and relaxed tail. Nothing in posture or expression suggests urgency."
        case .curious:
            base = "A head tilt, forward ears, and directed sniffing appear together when a dog is gathering new information. \(dogName) seems engaged with something unfamiliar."
        case .anxious, .fearful:
            base = "Tension and restless movement pair with high, uneven vocalization. The overall pattern reads as discomfort rather than a bid for attention."
        case .excited:
            base = "Energy is high across the board: springy movement, fast tail, and rapid shifts in focus. This usually reflects strong positive anticipation."
        case .alert:
            base = "A fixed stare, still body, and pricked ears mean something nearby has \(dogName)'s full attention. The posture is watchful, not relaxed."
        case .potentiallyThreatening:
            base = "A rigid stance, hard stare, and low growl are distance-increasing signals. These ask for space, so the priority is removing the trigger safely."
        case .unknown:
            base = "The available signals were too mixed or too brief to estimate a clear state. A longer or clearer capture would help."
        }

        let method = "This estimate is based on observable signals in the \(inputType.title.lowercased()) — sound, body language, and timing. It is not a literal translation of dog language and not a veterinary diagnosis."
        return base + " " + method
    }
}