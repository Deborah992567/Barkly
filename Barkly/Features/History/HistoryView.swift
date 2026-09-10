import SwiftUI

struct HistoryView: View {
    @Environment(AppContainer.self) private var app
    @State private var state: LoadState<[BehaviorAnalysis]> = .loading

    var body: some View {
        NavigationStack {
            Group {
                LoadableContainer(state: state, onRetry: { Task { await load() } }) { analyses in
                    populatedList(analyses)
                }
            }
            .background(BarklyColor.background.ignoresSafeArea())
            .navigationTitle("History")
            .navigationBarTitleDisplayMode(.large)
        }
        .task { await load() }
    }

    private func populatedList(_ analyses: [BehaviorAnalysis]) -> some View {
        if analyses.isEmpty {
            return AnyView(
                EmptyStateView(
                    icon: "clock",
                    title: "No analyses yet",
                    message: "Record a sound or analyze a video, and your history will show up here.",
                    actionTitle: "Analyze Your Dog",
                    action: {
                        Haptics.light()
                        app.openAnalyzer(.record)
                    }
                )
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            )
        }
        return AnyView(
            ScrollView {
                LazyVStack(spacing: BarklySpacing.md) {
                    ForEach(analyses) { analysis in
                        NavigationLink(value: analysis) {
                            HistoryRow(
                                analysis: analysis,
                                dog: app.dogs.first { $0.id == analysis.dogID }
                            )
                        }
                        .buttonStyle(HistoryRowLinkStyle())
                    }
                }
                .padding(.horizontal, BarklySpacing.pagePadding)
                .padding(.top, BarklySpacing.sm)
                .padding(.bottom, BarklySpacing.xl)
            }
            .navigationDestination(for: BehaviorAnalysis.self) { analysis in
                AnalysisResultView(
                    analysis: analysis,
                    dog: app.dogs.first { $0.id == analysis.dogID },
                    showsActions: false,
                    onDone: {}
                )
            }
        )
    }

    private func load() async {
        state = .loading
        do {
            let analyses = try await app.historyRepository.fetchAllAnalyses()
            state = .loaded(analyses)
        } catch {
            let failure = ErrorMapper.failure(for: error)
            state = ErrorMapper.isOffline(error) ? .offline(failure) : .failed(failure)
        }
    }
}

private struct HistoryRow: View {
    let analysis: BehaviorAnalysis
    let dog: Dog?

    var body: some View {
        HStack(spacing: BarklySpacing.md) {
            if let dog {
                DogAvatar(dog: dog, size: 48)
            } else {
                ZStack {
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(BarklyColor.cosmicOrangeSoft)
                        .frame(width: 48, height: 48)
                    Image(systemName: "questionmark")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                }
                .accessibilityHidden(true)
            }
            VStack(alignment: .leading, spacing: 2) {
                Text(dog?.name ?? "Unknown dog")
                    .font(BarklyFont.label)
                    .foregroundStyle(BarklyColor.primaryText)
                Text("\(analysis.inputType.shortTitle) \u{00B7} \(analysis.estimatedState.shortName)")
                    .font(BarklyFont.caption)
                    .foregroundStyle(BarklyColor.secondaryText)
                Text(BarklyDateFormatter.dateAndTime(analysis.createdAt))
                    .font(BarklyFont.caption)
                    .foregroundStyle(BarklyColor.tertiaryText)
            }
            Spacer(minLength: BarklySpacing.sm)
            VStack(alignment: .trailing, spacing: 2) {
                Text("\(analysis.confidencePercent)%")
                    .font(.system(size: 17, weight: .bold, design: .rounded))
                    .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                Text("estimate")
                    .font(BarklyFont.caption)
                    .foregroundStyle(BarklyColor.tertiaryText)
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel("\(analysis.confidencePercent) percent confidence")
        }
        .padding(BarklySpacing.md)
        .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
        )
        .accessibilityElement(children: .combine)
        .accessibilityHint("Opens the full result")
    }
}

private struct HistoryRowLinkStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .opacity(configuration.isPressed ? 0.9 : 1)
    }
}

#Preview("Populated") {
    let container = AppContainer()
    return HistoryView()
        .environment(container)
}