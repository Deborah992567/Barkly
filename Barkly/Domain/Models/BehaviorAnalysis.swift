import Foundation

struct BehaviorAnalysis: Identifiable, Hashable, Codable, Sendable {
    let id: UUID
    let dogID: UUID
    let createdAt: Date
    let inputType: AnalysisInputType
    let status: AnalysisStatus
    let failureMessage: String?
    let vocalizationType: VocalizationType?
    let estimatedState: BehaviorState
    let confidence: Float
    let observations: [String]
    let explanation: String
    let secondaryBehaviors: [BehaviorState]
    let safetyNote: String?
    let modelName: String?
    let modelVersion: String?
    let isInsufficientEvidence: Bool

    init(
        id: UUID = UUID(),
        dogID: UUID,
        createdAt: Date = Date(),
        inputType: AnalysisInputType,
        status: AnalysisStatus = .completed,
        failureMessage: String? = nil,
        vocalizationType: VocalizationType? = nil,
        estimatedState: BehaviorState,
        confidence: Float,
        observations: [String],
        explanation: String,
        secondaryBehaviors: [BehaviorState] = [],
        safetyNote: String? = nil,
        modelName: String? = nil,
        modelVersion: String? = nil,
        isInsufficientEvidence: Bool = false
    ) {
        self.id = id
        self.dogID = dogID
        self.createdAt = createdAt
        self.inputType = inputType
        self.status = status
        self.failureMessage = failureMessage
        self.vocalizationType = vocalizationType
        self.estimatedState = estimatedState
        self.confidence = confidence
        self.observations = observations
        self.explanation = explanation
        self.secondaryBehaviors = secondaryBehaviors
        self.safetyNote = safetyNote
        self.modelName = modelName
        self.modelVersion = modelVersion
        self.isInsufficientEvidence = isInsufficientEvidence
    }

    /// Whether the analysis finished and produced a usable (even if UNKNOWN)
    /// interpretation rather than failing or still being in-flight.
    var isUsableResult: Bool {
        status == .completed
    }

    var confidencePercent: Int {
        Int((confidence * 100).rounded())
    }
}