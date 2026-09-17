import SwiftUI

struct AnalysisResultView: View {
    let analysis: BehaviorAnalysis
    let dog: Dog?
    var showsActions: Bool = true
    let onDone: () -> Void

    @Environment(AppContainer.self) private var app
    @State private var feedbackSubmitted = false
    @State private var isSubmittingFeedback = false
    @State private var feedbackError: AppFailure?
    @State private var needsCorrection = false
    @State private var correction: BehaviorState?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                SectionHeader(
                    title: "BARKLY's Interpretation",
                    subtitle: "An estimate based on what it can observe"
                )

                interpretationCard

                insufficientEvidenceNote

                observationsSection

                secondarySection

                whySection

                if let safetyNote = analysis.safetyNote {
                    safetyNoteSection(safetyNote)
                }

                disclaimerSection

                if app.feedbackRepository != nil {
                    feedbackSection
                }

                if showsActions {
                    actions
                }
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.top, BarklySpacing.sm)
            .padding(.bottom, BarklySpacing.xl)
        }
        .background(BarklyColor.background.ignoresSafeArea())
        .navigationTitle("Result")
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(BarklyColor.background, for: .navigationBar)
    }

    private var interpretationCard: some View {
        BarklyCard {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .center, spacing: BarklySpacing.lg) {
                    interpretationText
                    ConfidenceRing(confidence: analysis.confidence)
                }
                VStack(alignment: .leading, spacing: BarklySpacing.lg) {
                    interpretationText
                    ConfidenceRing(confidence: analysis.confidence)
                        .frame(maxWidth: .infinity)
                }
            }
        }
    }

    private var interpretationText: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.sm) {
            Text("Estimated behavior")
                .font(BarklyFont.caption)
                .foregroundStyle(BarklyColor.tertiaryText)
            Text(analysis.estimatedState.estimatedTitle)
                .font(BarklyFont.displayHeading)
                .foregroundStyle(BarklyColor.primaryText)
                .fixedSize(horizontal: false, vertical: true)
            HStack(spacing: BarklySpacing.xs) {
                Circle()
                    .fill(analysis.estimatedState.accentColor)
                    .frame(width: 8, height: 8)
                Text(analysis.estimatedState.shortName)
                    .font(BarklyFont.label)
                    .foregroundStyle(BarklyColor.secondaryText)
                Text("\u{00B7} \(analysis.inputType.title.lowercased())")
                    .font(BarklyFont.label)
                    .foregroundStyle(BarklyColor.secondaryText)
            }
            .accessibilityElement(children: .combine)
        }
    }

    private var observationsSection: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            SectionHeader(title: "Key observations")
            VStack(spacing: 2) {
                ForEach(analysis.observations, id: \.self) { observation in
                    HStack(alignment: .top, spacing: BarklySpacing.md) {
                        Image(systemName: "checkmark")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                            .frame(width: 26, height: 26)
                            .background(BarklyColor.cosmicOrangeSoft, in: Circle())
                            .accessibilityHidden(true)
                        Text(observation)
                            .font(BarklyFont.body)
                            .foregroundStyle(BarklyColor.primaryText)
                            .padding(.top, BarklySpacing.xs)
                        Spacer(minLength: 0)
                    }
                    .padding(.vertical, BarklySpacing.sm)
                    if observation != analysis.observations.last {
                        Divider()
                            .overlay(BarklyColor.divider)
                    }
                }
            }
            .padding(.horizontal, BarklySpacing.md)
            .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                    .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
            )
        }
    }

    private var whySection: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            SectionHeader(title: "Why BARKLY thinks this")
            VStack(alignment: .leading, spacing: BarklySpacing.sm) {
                Text(analysis.explanation)
                    .font(BarklyFont.body)
                    .foregroundStyle(BarklyColor.primaryText)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(BarklySpacing.cardPadding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(BarklyColor.surface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
        }
    }

    private var disclaimerSection: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.sm) {
            HStack(alignment: .top, spacing: BarklySpacing.sm) {
                Image(systemName: "info.circle")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundStyle(BarklyColor.tertiaryText)
                    .padding(.top, 1)
                Text("BARKLY provides behavioral estimates based on observable signals — sound, body language, and context. It does not literally translate dog language, and it does not provide veterinary or medical diagnosis.")
                    .font(BarklyFont.footnote)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(BarklySpacing.md)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(BarklyColor.surface, in: RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous))
        }
        .accessibilityElement(children: .combine)
    }

    @ViewBuilder
    private var insufficientEvidenceNote: some View {
        if analysis.isInsufficientEvidence {
            VStack(alignment: .leading, spacing: BarklySpacing.sm) {
                HStack(alignment: .top, spacing: BarklySpacing.sm) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 15, weight: .medium))
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                        .padding(.top, 1)
                    Text("The signals were too weak to reach a confident estimate. A clearer recording with more of the moment would help.")
                        .font(BarklyFont.footnote)
                        .foregroundStyle(BarklyColor.secondaryText)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .padding(BarklySpacing.md)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(BarklyColor.cosmicOrangeSoft, in: RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous))
        }
    }

    @ViewBuilder
    private var secondarySection: some View {
        if !analysis.secondaryBehaviors.isEmpty {
            VStack(alignment: .leading, spacing: BarklySpacing.md) {
                SectionHeader(title: "Also read as")
                Text(analysis.secondaryBehaviors.map(\.shortName).joined(separator: " · "))
                    .font(BarklyFont.body)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private func safetyNoteSection(_ note: String) -> some View {
        VStack(alignment: .leading, spacing: BarklySpacing.sm) {
            HStack(alignment: .top, spacing: BarklySpacing.sm) {
                Image(systemName: "shield.lefthalf.filled")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundStyle(BarklyColor.tertiaryText)
                    .padding(.top, 1)
                Text(note)
                    .font(BarklyFont.footnote)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(BarklySpacing.md)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(BarklyColor.surface, in: RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous))
        }
    }

    private var feedbackSection: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            SectionHeader(
                title: "Help BARKLY learn",
                subtitle: "Your feedback improves future estimates"
            )

            if feedbackSubmitted {
                Label("Thanks — your feedback was recorded.", systemImage: "checkmark.circle.fill")
                    .font(BarklyFont.body)
                    .foregroundStyle(BarklyColor.primaryText)
                    .frame(maxWidth: .infinity, alignment: .leading)
            } else if needsCorrection {
                correctionForm
            } else {
                HStack(spacing: BarklySpacing.md) {
                    feedbackButton(
                        title: "Looks right",
                        icon: "hand.thumbsup.fill",
                        color: BarklyColor.cosmicOrangeDeep
                    ) {
                        submit(verdict: .confirmed, corrected: nil)
                    }
                    feedbackButton(
                        title: "Was off",
                        icon: "hand.thumbsdown.fill",
                        color: BarklyColor.error
                    ) {
                        needsCorrection = true
                    }
                }
            }

            if let feedbackError {
                HStack(alignment: .top, spacing: BarklySpacing.md) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(BarklyColor.error)
                        .accessibilityHidden(true)
                    VStack(alignment: .leading, spacing: BarklySpacing.xs) {
                        Text(feedbackError.message)
                            .font(BarklyFont.caption)
                            .foregroundStyle(BarklyColor.secondaryText)
                        Button("Try Again") {
                            Haptics.light()
                            if needsCorrection {
                                if let correction {
                                    submit(verdict: .corrected, corrected: correction)
                                }
                            } else {
                                submit(verdict: .confirmed, corrected: nil)
                            }
                        }
                        .font(BarklyFont.label)
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .accessibilityElement(children: .combine)
                .accessibilityIdentifier("feedback_error")
            }
        }
    }

    private var correctionForm: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            Text("What was it really?")
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.primaryText)
            Menu {
                ForEach(BehaviorState.allCases, id: \.self) { state in
                    Button(state.shortName) {
                        correction = state
                    }
                }
            } label: {
                HStack {
                    Text(correction?.shortName ?? "Choose a behavior")
                        .foregroundStyle(correction == nil ? BarklyColor.secondaryText : BarklyColor.primaryText)
                    Spacer()
                    Image(systemName: "chevron.up.chevron.down")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(BarklyColor.tertiaryText)
                }
                .font(BarklyFont.body)
                .padding(BarklySpacing.md)
                .background(BarklyColor.surface, in: RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous)
                        .strokeBorder(BarklyColor.divider.opacity(0.7), lineWidth: 1)
                )
            }
            HStack(spacing: BarklySpacing.md) {
                BarklyButton(title: "Submit correction", icon: "checkmark", style: .tinted) {
                    guard let correction else { return }
                    submit(verdict: .corrected, corrected: correction)
                }
                Button("Cancel") {
                    needsCorrection = false
                    correction = nil
                }
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.secondaryText)
            }
        }
    }

    private func feedbackButton(title: String, icon: String, color: Color, action: @escaping () -> Void) -> some View {
        Button {
            Haptics.light()
            action()
        } label: {
            HStack(spacing: BarklySpacing.sm) {
                Image(systemName: icon)
                Text(title)
                    .font(BarklyFont.label)
            }
            .foregroundStyle(color)
            .frame(maxWidth: .infinity)
            .frame(height: 48)
            .background(BarklyColor.surface, in: Capsule())
            .overlay(
                Capsule().strokeBorder(BarklyColor.divider.opacity(0.7), lineWidth: 1)
            )
            .contentShape(Capsule())
        }
        .buttonStyle(BarklyRowPressStyle())
    }

    private func submit(verdict: FeedbackVerdict, corrected: BehaviorState?) {
        guard let repository = app.feedbackRepository, !isSubmittingFeedback else { return }
        isSubmittingFeedback = true
        feedbackError = nil
        Task {
            do {
                try await repository.submit(
                    for: analysis.id,
                    verdict: verdict,
                    correctedBehavior: corrected,
                    comment: nil
                )
                guard !Task.isCancelled else { return }
                feedbackSubmitted = true
            } catch {
                guard !Task.isCancelled else { return }
                feedbackError = ErrorMapper.failure(for: error)
            }
            isSubmittingFeedback = false
        }
    }

    private var actions: some View {
        VStack(spacing: BarklySpacing.sm) {
            BarklyButton(title: "Done", icon: "checkmark") {
                Haptics.success()
                onDone()
            }
            Button {
                Haptics.light()
                onDone()
                app.openTab(.history)
            } label: {
                Text("View in History")
                    .font(BarklyFont.label)
                    .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                    .frame(minHeight: 44)
                    .frame(maxWidth: .infinity)
            }
            .accessibilityHint("Saves this result and opens your history")
        }
        .padding(.top, BarklySpacing.xs)
    }
}

#Preview("Result") {
    let container = AppContainer()
    let dog = container.selectedDog
    return NavigationStack {
        AnalysisResultView(
            analysis: BehaviorAnalysis(
                dogID: dog?.id ?? UUID(),
                inputType: .audio,
                vocalizationType: .bark,
                estimatedState: .attentionSeeking,
                confidence: 0.82,
                observations: [
                    "Repeated vocalization",
                    "Short intervals between sounds",
                    "Alert posture",
                    "Movement toward owner"
                ],
                explanation: "The sounds arrived in short, regular bursts while Max faced your direction. Regular timing plus forward attention most often means your dog is trying to start an interaction."
            ),
            dog: dog,
            onDone: {}
        )
    }
    .environment(container)
}