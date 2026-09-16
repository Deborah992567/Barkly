import Foundation

/// Demo recorder: produces a tiny valid WAV so the flow control path is
/// exercised end-to-end, but the demo analysis repository never reads it.
final class MockAudioRecorder: AudioRecording {
    private var fileURL: URL?

    var isRecording: Bool {
        fileURL != nil
    }

    func start() throws {
        guard fileURL == nil else { return }
        fileURL = URL.temporaryDirectory
            .appendingPathComponent("barkly-demo-\(UUID().uuidString)")
            .appendingPathExtension("wav")
        FileManager.default.createFile(atPath: fileURL!.path, contents: Self.silenceWAV)
    }

    func stop() throws -> URL {
        guard let fileURL else { throw AudioRecordError.notRecording }
        self.fileURL = nil
        return fileURL
    }

    /// 0.5 s of 44.1 kHz 16-bit mono silence.
    private static let silenceWAV: Data = {
        let sampleRate: UInt32 = 44_100
        let seconds: UInt32 = 1
        let dataSize: UInt32 = sampleRate * seconds * 2
        let byteRate: UInt32 = sampleRate * 2

        var header = Data()
        func append(_ value: String) { header.append(Data(value.utf8)) }
        func append(_ value: UInt32) { header.append(contentsOf: u32(value)) }
        func append(_ value: UInt16) { header.append(contentsOf: u16(value)) }

        append("RIFF")
        append(36 + dataSize)
        append("WAVE")
        append("fmt ")
        append(UInt32(16))
        append(UInt16(1))
        append(UInt16(1))
        append(sampleRate)
        append(byteRate)
        append(UInt16(2))
        append(UInt16(16))
        append("data")
        append(dataSize)

        return header + Data(count: Int(dataSize))
    }()

    private static func u32(_ value: UInt32) -> [UInt8] {
        [UInt8(value & 0xFF), UInt8((value >> 8) & 0xFF), UInt8((value >> 16) & 0xFF), UInt8((value >> 24) & 0xFF)]
    }

    private static func u16(_ value: UInt16) -> [UInt8] {
        [UInt8(value & 0xFF), UInt8((value >> 8) & 0xFF)]
    }
}