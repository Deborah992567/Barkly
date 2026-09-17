import SwiftUI

struct HistoryView: View {
    @Environment(AppContainer.self) private var app
    @State private var pager: HistoryPager?

    var body: some View {
        NavigationStack {
            Group {
                if let pager {
                    content(for: pager)
                } else {
                    LoadingStateView()
                }
            }
            .background(BarklyColor.background.ignoresSafeArea())
            .navigationTitle("History")
            .navigationBarTitleDisplayMode(.large)
            .navigationDestination(for: BehaviorAnalysis.self) { analysis in
                AnalysisResultView(
                    analysis: analysis,
                    dog: app.dogs.first { $0.id == analysis.dogID },
                    showsActions: false,
                    onDone: {}
                )
            }
        }
        .task {
            if pager == nil {
                let created = HistoryPager(repository: app.historyRepository)
                pager = created
                await created.loadInitial()
            }
        }
        .onAppear {
            guard let pager else { return }
            Task { await pager.loadInitial() }
        }
    }

    @ViewBuilder
    private func content(for pager: HistoryPager) -> some View {
        switch pager.phase {
        case .loading:
            LoadingStateView()
        case .empty:
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
            .accessibilityIdentifier("history_empty")
        case .failed(let failure):
            ErrorStateView(failure: failure) {
                Task { await pager.loadInitial() }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .accessibilityIdentifier("history_error")
        case .offline(let failure):
            OfflineStateView(failure: failure) {
                Task { await pager.loadInitial() }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .accessibilityIdentifier("history_offline")
        case .loaded(let hasNext):
            populatedList(pager: pager, hasNext: hasNext)
        }
    }

    private func populatedList(pager: HistoryPager, hasNext: Bool) -> some View {
        ScrollView {
            LazyVStack(spacing: BarklySpacing.md) {
                ForEach(pager.items) { analysis in
                    if analysis.isUsableResult {
                        NavigationLink(value: analysis) {
                            HistoryRow(analysis: analysis, dog: app.dogs.first { $0.id == analysis.dogID })
                        }
                        .buttonStyle(HistoryRowLinkStyle())
                    } else {
                        HistoryStatusRow(analysis: analysis, dog: app.dogs.first { $0.id == analysis.dogID })
                    }
                }

                footer(pager: pager, hasNext: hasNext)
                    .padding(.top, BarklySpacing.xs)
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.top, BarklySpacing.sm)
            .padding(.bottom, BarklySpacing.xl)
        }
        .refreshable {
            await pager.refresh()
        }
        .accessibilityIdentifier("history_list")
    }

    @ViewBuilder
    private func footer(pager: HistoryPager, hasNext: Bool) -> some View {
        if pager.isLoadingMore {
            ProgressView()
                .tint(BarklyColor.cosmicOrange)
                .padding(.vertical, BarklySpacing.md)
                .accessibilityLabel("Loading more analyses")
        } else if let failure = pager.moreFailure {
            VStack(spacing: BarklySpacing.sm) {
                Text(failure.message)
                    .font(BarklyFont.caption)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .multilineTextAlignment(.center)
                Button("Try Again") {
                    Haptics.light()
                    Task { await pager.retryNextPage() }
                }
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                .frame(minHeight: 44)
            }
            .frame(maxWidth: .infinity)
        } else if hasNext {
            Color.clear
                .frame(height: 1)
                .onAppear {
                    Task { await pager.loadNextPage() }
                }
        } else {
            Text("That's every analysis so far.")
                .font(BarklyFont.caption)
                .foregroundStyle(BarklyColor.tertiaryText)
                .frame(maxWidth: .infinity)
                .padding(.top, BarklySpacing.xs)
                .accessibilityIdentifier("history_end")
        }
    }
}

private struct HistoryRow: View {
    let analysis: BehaviorAnalysis
    let dog: Dog?

    var body: some View {
        HistoryRowChrome(dog: dog) {
            VStack(alignment: .leading, spacing: 2) {
                Text(dog?.name ?? "Unknown dog")
                    .font(BarklyFont.label)
                    .foregroundStyle(BarklyColor.primaryText)
                Text("\(analysis.inputType.shortTitle) \u{00B7} \(analysis.estimatedState.shortName)")
                    .font(BarklyFont.caption)
                    .foregroundStyle(BarklyColor.secondaryText)
                if analysis.isInsufficientEvidence {
                    Text("Limited evidence")
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.warning)
                }
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
        .accessibilityElement(children: .combine)
        .accessibilityHint("Opens the full result")
    }
}

/// Non-navigable row for analyses that are still running, failed, or cancelled.
/// These must never look like a completed interpretation.
private struct HistoryStatusRow: View {
    let analysis: BehaviorAnalysis
    let dog: Dog?

    var body: some View {
        HistoryRowChrome(dog: dog) {
            VStack(alignment: .leading, spacing: 2) {
                Text(dog?.name ?? "Unknown dog")
                    .font(BarklyFont.label)
                    .foregroundStyle(BarklyColor.primaryText)
                Text(statusTitle)
                    .font(BarklyFont.caption)
                    .foregroundStyle(statusColor)
                if let detail = statusDetail {
                    Text(detail)
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.tertiaryText)
                        .lineLimit(2)
                }
            }
            Spacer(minLength: BarklySpacing.sm)
            statusBadge
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(dog?.name ?? "Unknown dog"), \(statusTitle)")
    }

    private var statusTitle: String {
        switch analysis.status {
        case .created, .queued, .processing: "Analyzing…"
        case .failed: "Analysis failed"
        case .cancelled: "Cancelled"
        case .completed: "Completed"
        }
    }

    private var statusDetail: String? {
        switch analysis.status {
        case .failed: analysis.failureMessage
        case .created, .queued, .processing, .cancelled, .completed: nil
        }
    }

    private var statusColor: Color {
        switch analysis.status {
        case .failed: BarklyColor.error
        case .cancelled: BarklyColor.secondaryText
        case .created, .queued, .processing: BarklyColor.info
        case .completed: BarklyColor.secondaryText
        }
    }

    @ViewBuilder
    private var statusBadge: some View {
        switch analysis.status {
        case .created, .queued, .processing:
            ProgressView()
                .tint(BarklyColor.cosmicOrange)
                .accessibilityHidden(true)
        case .failed:
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(BarklyColor.error)
                .accessibilityHidden(true)
        case .cancelled:
            Image(systemName: "xmark.circle.fill")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(BarklyColor.tertiaryText)
                .accessibilityHidden(true)
        case .completed:
            EmptyView()
        }
    }
}

private struct HistoryRowChrome<Content: View>: View {
    let dog: Dog?
    @ViewBuilder let content: Content

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
            content
        }
        .padding(BarklySpacing.md)
        .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
        )
    }
}

private struct HistoryRowLinkStyle: ButtonStyle {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(reduceMotion ? 1 : (configuration.isPressed ? 0.985 : 1))
            .opacity(configuration.isPressed ? 0.9 : 1)
    }
}

#Preview("Populated") {
    HistoryView()
        .environment(AppContainer(dependencies: .demo))
}