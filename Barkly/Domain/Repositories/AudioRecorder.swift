import Foundation
import AVFoundation

enum AudioRecordError: Error, LocalizedError {
    case alreadyRecording
    case notRecording
    case setupFailed(String)
    case pipelineUnavailable

    var errorDescription: String? {
        switch self {
        case .alreadyRecording: "A recording is already in progress."
        case .notRecording: "There's no active recording to stop."
        case .setupFailed(let message): "The recorder couldn't start: \(message)"
        case .pipelineUnavailable: "The microphone is busy with another app."
        }
    }
}

/// Captures dog sounds to a WAV file on disk, ready for the backend's
/// audio pipeline without any transcoding.
protocol AudioRecording: Sendable {
    var isRecording: Bool { get }
    func start() throws
    func stop() throws -> URL
}

final class RealAudioRecorder: AudioRecording, @unchecked Sendable {
    private let lock = NSLock()
    private var recorder: AVAudioRecorder?
    private var temporaryURL: URL?

    var isRecording: Bool {
        lock.lock()
        defer { lock.unlock() }
        return recorder?.isRecording ?? false
    }

    func start() throws {
        lock.lock()
        defer { lock.unlock() }
        guard recorder == nil else { throw AudioRecordError.alreadyRecording }

        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.record, mode: .default)
            try session.setActive(true)
        } catch {
            throw AudioRecordError.pipelineUnavailable
        }

        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("barkly-rec-\(UUID().uuidString)")
            .appendingPathExtension("wav")

        let settings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatLinearPCM),
            AVSampleRateKey: 44_100.0,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false,
        ]

        do {
            let recorder = try AVAudioRecorder(url: url, settings: settings)
            recorder.isMeteringEnabled = true
            recorder.prepareToRecord()
            guard recorder.record() else {
                throw AudioRecordError.setupFailed("The recorder declined to start.")
            }
            self.recorder = recorder
            temporaryURL = url
        } catch let error as AudioRecordError {
            try? session.setActive(false)
            throw error
        } catch {
            try? session.setActive(false)
            throw AudioRecordError.setupFailed(String(describing: error))
        }
    }

    func stop() throws -> URL {
        lock.lock()
        defer { lock.unlock() }
        guard let recorder else { throw AudioRecordError.notRecording }
        recorder.stop()
        self.recorder = nil
        try? AVAudioSession.sharedInstance().setActive(false)
        guard let url = temporaryURL else { throw AudioRecordError.setupFailed("No file was produced.") }
        temporaryURL = nil
        return url
    }
}