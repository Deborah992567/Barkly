import SwiftUI

/// Captures behavior notes/context (no media) and runs a behavior analysis.
struct BehaviorFlowView: View {
    let onDone: () -> Void

    @Environment(AppContainer.self) private var app
    @State private var controller: AnalysisFlowController?
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
        .sheet(isPresented: $showContextSheet) {
            AnalysisContextSheet(context: $context)
        }
        .task {
            if controller == nil {
                let flow = AnalysisFlowController(container: app)
                flow.pendingContext = context
                controller = flow
                await flow.begin(route: .upload)
                flow.pendingContext = context
            }
        }
        .onChange(of: context) { _, newValue in
            Task { @MainActor in
                controller?.pendingContext = newValue
            }
        }
    }

    @ViewBuilder
    private func content(for controller: AnalysisFlowController) -> some View {
        switch controller.phase {
        case .idle:
            notesContent
        case .processing:
            AnalysisProcessingView(caption: "Reading the observed behavior")
        case .ready(let analysis):
            AnalysisResultView(
                analysis: analysis,
                dog: app.selectedDog,
                onDone: onDone
            )
        case .failed(let failure):
            ErrorStateView(failure: AppFailure(
                title: failure.title,
                message: failure.message,
                hint: failure.hint,
                recovery: mapRecovery(failure.recovery)
            )) {
                controller.resetToSelection()
            }
            .padding(BarklySpacing.lg)
        case .requestingPermission, .recording:
            Color.clear
        }
    }

    private var notesContent: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                SectionHeader(
                    title: "Describe the moment",
                    subtitle: "Tell BARKLY what you observed, then estimate."
                )

                BarklyCard {
                    VStack(alignment: .leading, spacing: BarklySpacing.md) {
                        Text("Context (optional)")
                            .font(BarklyFont.cardTitle)
                            .foregroundStyle(BarklyColor.primaryText)

                        Label("What was the dog doing?", systemImage: "slider.horizontal.3")
                            .font(BarklyFont.body)
                            .foregroundStyle(BarklyColor.primaryText)

                        BarklyButton(
                            title: configuredContext ? "Edit context" : "Add context",
                            icon: "slider.horizontal.3",
                            style: .tinted
                        ) {
                            Haptics.light()
                            showContextSheet = true
                        }
                    }
                }

                BarklyButton(title: "Estimate behavior", icon: "eye.fill") {
                    Haptics.medium()
                    Task {
                        await controller?.requestBehaviorAnalysis(context: context)
                    }
                }
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.top, BarklySpacing.sm)
            .padding(.bottom, BarklySpacing.xl)
        }
    }

    private var configuredContext: Bool {
        context != .empty
    }

    private func mapRecovery(_ recovery: AnalysisFlowController.AnalysisError.Recovery) -> AppFailure.Recovery? {
        switch recovery {
        case .retry: return .retry
        case .openSettings: return .openSettings
        case .none: return nil
        }
    }
}