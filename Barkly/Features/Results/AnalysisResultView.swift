import SwiftUI

struct AnalysisResultView: View {
    let analysis: BehaviorAnalysis
    let dog: Dog?
    var showsActions: Bool = true
    let onDone: () -> Void

    @Environment(AppContainer.self) private var app

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                SectionHeader(
                    title: "BARKLY's Interpretation",
                    subtitle: "An estimate based on what it can observe"
                )

                interpretationCard

                observationsSection

                whySection

                disclaimerSection

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