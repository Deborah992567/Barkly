import Foundation
import Observation

@MainActor
@Observable
final class AnalysisFlowController {
    enum Phase: Equatable {
        case idle
        case requestingPermission
        case recording
        case processing
        case ready(BehaviorAnalysis)
        case failed(AnalysisError)
    }

    struct AnalysisError: Equatable {
        let title: String
        let message: String
        var hint: String? = nil
        var recovery: Recovery

        enum Recovery: Equatable {
            case retry
            case openSettings
            case none
        }
    }

    private let container: AppContainer
    private let recorder: any AudioRecording
    private(set) var phase: Phase = .idle
    private(set) var inputType: AnalysisInputType?
    private(set) var recordedURL: URL?
    var pendingContext: AnalysisContextInput? = nil

    init(container: AppContainer) {
        self.container = container
        self.recorder = container.audioRecorder
    }

    var recordingStarts: Bool {
        phase == .recording
    }

    var isProcessing: Bool {
        phase == .processing
    }

    var result: BehaviorAnalysis? {
        guard case .ready(let analysis) = phase else { return nil }
        return analysis
    }

    func begin(route: AnalysisPath) async {
        switch route {
        case .record:
            inputType = .audio
            await requestMicrophone()
        case .video:
            inputType = .video
            phase = .idle
        case .upload:
            inputType = .photo
            phase = .idle
        }
    }

    func callPermissionExplainerShown() async {
        if inputType == .audio {
            await requestMicrophone()
        }
    }

    func resetToSelection() {
        phase = .idle
    }

    func startRecording() async {
        if await recorder.isRecording {
            return
        }
        recordedURL = nil
        do {
            try await recorder.start()
            phase = .recording
        } catch {
            phase = .failed(recorderError(error))
        }
    }

    private func requestMicrophone() async {
        let status = await container.permissionService.status(for: .microphone)
        switch status {
        case .granted:
            await startRecording()
        case .notDetermined:
            phase = .requestingPermission
        case .denied, .restricted, .unavailable:
            phase = .failed(micDeniedError)
        }
    }

    func grantMicrophone() async {
        let status = await container.permissionService.requestAccess(for: .microphone)
        switch status {
        case .granted:
            await startRecording()
        case .denied, .restricted, .unavailable:
            phase = .failed(micDeniedError)
        case .notDetermined:
            phase = .requestingPermission
        }
    }

    private var micDeniedError: AnalysisError {
        AnalysisError(
            title: "Microphone access needed",
            message: "BARKLY uses the microphone to capture your dog's sounds for analysis. Enable microphone access to record.",
            hint: "Allow microphone access in Settings, then come back to record.",
            recovery: .openSettings
        )
    }

    private func recorderError(_ error: Error) -> AnalysisError {
        AnalysisError(
            title: "Couldn't start recording",
            message: (error as? LocalizedError)?.errorDescription ?? "The microphone couldn't start.",
            hint: "If another app is using the microphone, close it and try again.",
            recovery: .retry
        )
    }

    /// Ends the on-device recording and submits the captured audio.
    func submitRecording(duration: TimeInterval) async {
        do {
            let url = try await recorder.stop()
            recordedURL = url
            await submit(
                inputType: .audio,
                mediaURLs: [url],
                duration: duration,
                context: pendingContext
            )
        } catch {
            phase = .failed(recorderError(error))
        }
    }

    /// Submits a behavior-observation analysis (no media) with optional context.
    func requestBehaviorAnalysis(context: AnalysisContextInput?) async {
        pendingContext = context
        guard let dogID = container.selectedDogID else {
            phase = .failed(AnalysisError(
                title: "No dog selected",
                message: "Choose a dog first, then try the analysis again.",
                recovery: .retry
            ))
            return
        }
        phase = .processing
        do {
            let analysis = try await container.analysisRepository.requestBehaviorAnalysis(
                for: dogID,
                context: pendingContext
            )
            try await container.historyRepository.record(analysis)
            phase = .ready(analysis)
        } catch let error as AppRepositoryError {
            phase = .failed(map(error))
        } catch {
            phase = .failed(AnalysisError(
                title: "Analysis unavailable",
                message: "Something went wrong while reading the signal. Please try again.",
                recovery: .retry
            ))
        }
    }

    /// Submits an analysis for media already captured (video or photo files).
    func submit(inputType: AnalysisInputType, mediaURLs: [URL], duration: TimeInterval? = nil) async {
        await submit(
            inputType: inputType,
            mediaURLs: mediaURLs,
            duration: duration,
            context: pendingContext
        )
    }

    /// Middleware path used by callers that captured in-memory media only.
    func submit(inputType: AnalysisInputType) async {
        await submit(inputType: inputType, mediaURLs: [], duration: nil)
    }

    private func submit(
        inputType: AnalysisInputType,
        mediaURLs: [URL] = [],
        duration: TimeInterval? = nil,
        context: AnalysisContextInput?
    ) async {
        guard let dogID = container.selectedDogID else {
            phase = .failed(AnalysisError(
                title: "No dog selected",
                message: "Choose a dog first, then try the analysis again.",
                recovery: .retry
            ))
            return
        }

        phase = .processing
        do {
            let analysis: BehaviorAnalysis
            if inputType == .behavior {
                analysis = try await container.analysisRepository.requestBehaviorAnalysis(
                    for: dogID,
                    context: context
                )
            } else {
                analysis = try await container.analysisRepository.requestAnalysis(
                    for: dogID,
                    inputType: inputType,
                    mediaURLs: mediaURLs,
                    duration: duration,
                    context: context
                )
            }
            try await container.historyRepository.record(analysis)
            phase = .ready(analysis)
        } catch let error as AppRepositoryError {
            phase = .failed(map(error))
        } catch {
            phase = .failed(AnalysisError(
                title: "Analysis unavailable",
                message: "Something went wrong while reading the signal. Please try again.",
                recovery: .retry
            ))
        }
    }

    private func map(_ error: AppRepositoryError) -> AnalysisError {
        switch error {
        case .offline:
            AnalysisError(
                title: "You're offline",
                message: "Analysis needs a connection to BARKLY's service. It will work once you're back online.",
                hint: "Everything stays safe on your device until then.",
                recovery: .retry
            )
        case .serviceUnavailable:
            AnalysisError(
                title: "Analysis unavailable right now",
                message: "BARKLY's analysis service isn't responding. Try again in a moment.",
                recovery: .retry
            )
        case .invalidData:
            AnalysisError(
                title: "Couldn't read the media",
                message: "The sound, video, or photo couldn't be processed. Try capturing it again.",
                recovery: .retry
            )
        case .permissionDenied:
            AnalysisError(
                title: "Access needed",
                message: "BARKLY needs access to this media to analyze it. You can allow access in Settings.",
                recovery: .openSettings
            )
        case .unauthorized:
            AnalysisError(
                title: "Session expired",
                message: "Sign in again to keep using BARKLY.",
                recovery: .retry
            )
        }
    }
}