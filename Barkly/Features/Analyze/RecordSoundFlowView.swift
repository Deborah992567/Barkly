import SwiftUI

struct RecordSoundFlowView: View {
    let onDone: () -> Void

    @Environment(AppContainer.self) private var app
    @State private var controller: AnalysisFlowController?
    @State private var startDate: Date?
    @State private var context = AnalysisContextInput.empty
    @State private var showContextSheet = false

    var body: some View {
        ZStack {
            BarklyColor.background
                .ignoresSafeArea()
            Group {
                if let controller {
                    content(for: controller)
                } else {
                    Color.clear
                }
            }
            .navigationBarTitleDisplayMode(.inline)
        }
        .navigationBarBackButtonHidden(false)
        .sheet(isPresented: $showContextSheet) {
            AnalysisContextSheet(context: $context)
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    Haptics.light()
                    showContextSheet = true
                } label: {
                    Label("Context", systemImage: "slider.horizontal.3")
                }
                .accessibilityHint("Add optional context about this moment")
            }
        }
        .onChange(of: context) { _, newValue in
            controller?.pendingContext = newValue
        }
        .task {
            if controller == nil {
                let newController = AnalysisFlowController(container: app)
                controller = newController
                await newController.begin(route: .record)
            }
        }
    }

    @ViewBuilder
    private func content(for controller: AnalysisFlowController) -> some View {
        switch controller.phase {
        case .requestingPermission:
            PermissionExplainerView(
                title: "Record your dog's sound",
                message: "BARKLY uses the microphone so you can capture a bark, whine, or other sound for estimation. Audio stays on your device.",
                allowTitle: "Enable Microphone",
                onAllow: {
                    await controller.grantMicrophone()
                },
                onNotNow: {
                    Haptics.light()
                    onDone()
                }
            )
        case .recording:
            recordingPanel
                .onAppear {
                    if startDate == nil {
                        startDate = Date()
                    }
                    Task {
                        await controller.startRecording()
                    }
                }
        case .processing:
            AnalysisProcessingView(caption: "BARKLY is reading the signals")
        case .ready(let analysis):
            AnalysisResultView(
                analysis: analysis,
                dog: app.selectedDog,
                onDone: onDone
            )
        case .failed(let failure):
            flowError(failure)
        case .idle:
            Color.clear
        }
    }

    private var recordingPanel: some View {
        VStack(spacing: BarklySpacing.lg) {
            Spacer()
            VStack(spacing: BarklySpacing.md) {
                ZStack {
                    Circle()
                        .fill(BarklyColor.cosmicOrangeSoft)
                        .frame(width: 128, height: 128)
                    Image(systemName: "mic.fill")
                        .font(.system(size: 44, weight: .medium))
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                }
                .accessibilityHidden(true)

                RecorderWaveform()

                Text("Recording")
                    .font(BarklyFont.heroTitle)
                    .foregroundStyle(BarklyColor.primaryText)
                    .accessibilityLabel("Recording in progress")

                TimelineView(.periodic(from: .now, by: 1)) { context in
                    let start = startDate ?? context.date
                    Text(format(context.date.timeIntervalSince(start)))
                        .font(.system(size: 28, weight: .semibold, design: .rounded))
                        .foregroundStyle(BarklyColor.secondaryText)
                        .monospacedDigit()
                }
                .frame(height: 34)
            }
            Spacer()
            VStack(spacing: BarklySpacing.md) {
                BarklyButton(title: "Stop & Analyze", icon: "stop.fill") {
                    stopRecording()
                }
                Button {
                    Haptics.light()
                    onDone()
                } label: {
                    Text("Cancel")
                        .font(BarklyFont.label)
                        .foregroundStyle(BarklyColor.secondaryText)
                        .frame(minHeight: 44)
                        .frame(maxWidth: .infinity)
                }
                .accessibilityHint("Stops and discards this recording")
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.bottom, BarklySpacing.lg)
        }
    }

    private func format(_ interval: TimeInterval) -> String {
        let totalSeconds = Int(interval)
        return String(format: "%02d:%02d", totalSeconds / 60, totalSeconds % 60)
    }

    @ViewBuilder
    private func flowError(_ failure: AnalysisFlowController.AnalysisError) -> some View {
        let appFailure = AppFailure(
            title: failure.title,
            message: failure.message,
            hint: failure.hint,
            recovery: mapRecovery(failure.recovery)
        )
        ErrorStateView(failure: appFailure) {
            Task {
                await retry(failure)
            }
        }
        .padding(BarklySpacing.lg)
    }

    private func mapRecovery(_ recovery: AnalysisFlowController.AnalysisError.Recovery) -> AppFailure.Recovery? {
        switch recovery {
        case .retry: return .retry
        case .openSettings: return .openSettings
        case .none: return nil
        }
    }

    private func retry(_ failure: AnalysisFlowController.AnalysisError) async {
        guard let controller else { return }
        await controller.begin(route: .record)
    }

    private func stopRecording() {
        guard let controller, let startDate else { return }
        let duration = Date().timeIntervalSince(startDate)
        self.startDate = nil
        Haptics.medium()
        Task {
            await controller.submitRecording(duration: duration)
        }
    }
}

struct RecorderWaveform: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var animate = false

    private let barCount = 5

    var body: some View {
        HStack(spacing: 8) {
            ForEach(0..<barCount, id: \.self) { index in
                RoundedRectangle(cornerRadius: 3, style: .continuous)
                    .fill(BarklyColor.cosmicOrange)
                    .frame(width: 7, height: reducedHeight(for: index))
                    .scaleEffect(y: reduceMotion ? 1 : (animate ? 1 : 0.4), anchor: .center)
                    .animation(
                        reduceMotion ? nil : .easeInOut(duration: 0.7).repeatForever(autoreverses: true).delay(Double(index) * 0.12),
                        value: animate
                    )
            }
        }
        .frame(height: 56)
        .onAppear { animate = true }
        .accessibilityHidden(true)
    }

    private func reducedHeight(for index: Int) -> CGFloat {
        switch index {
        case 1, 3: 42
        case 2: 52
        default: 26
        }
    }
}

#Preview("Recording") {
    NavigationStack {
        RecordSoundFlowView(onDone: {})
    }
    .environment(AppContainer())
}