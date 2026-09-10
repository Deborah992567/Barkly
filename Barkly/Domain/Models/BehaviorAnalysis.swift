import Foundation

struct BehaviorAnalysis: Identifiable, Hashable, Codable, Sendable {
    let id: UUID
    let dogID: UUID
    let createdAt: Date
    let inputType: AnalysisInputType
    let vocalizationType: VocalizationType?
    let estimatedState: BehaviorState
    let confidence: Float
    let observations: [String]
    let explanation: String

    init(
        id: UUID = UUID(),
        dogID: UUID,
        createdAt: Date = Date(),
        inputType: AnalysisInputType,
        vocalizationType: VocalizationType? = nil,
        estimatedState: BehaviorState,
        confidence: Float,
        observations: [String],
        explanation: String
    ) {
        self.id = id
        self.dogID = dogID
        self.createdAt = createdAt
        self.inputType = inputType
        self.vocalizationType = vocalizationType
        self.estimatedState = estimatedState
        self.confidence = confidence
        self.observations = observations
        self.explanation = explanation
    }

    var confidencePercent: Int {
        Int((confidence * 100).rounded())
    }
}