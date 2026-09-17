import SwiftUI

struct InsightsView: View {
    @Environment(AppContainer.self) private var app
    @State private var state: LoadState<InsightsSummary> = .loading
    @State private var showAddDog = false

    var body: some View {
        NavigationStack {
            Group {
                if app.selectedDog == nil {
                    EmptyStateView(
                        icon: "pawprint",
                        title: "Add a dog to see insights",
                        message: "Insights are kept per dog, so add one to start spotting patterns.",
                        actionTitle: "Add Your Dog",
                        action: {
                            Haptics.light()
                            showAddDog = true
                        }
                    )
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .accessibilityIdentifier("insights_no_dog")
                } else {
                    LoadableContainer(state: state, onRetry: { Task { await load() } }) { insights in
                        populatedContent(insights)
                    }
                }
            }
            .background(BarklyColor.background.ignoresSafeArea())
            .navigationTitle("Insights")
            .navigationBarTitleDisplayMode(.large)
            .sheet(isPresented: $showAddDog) {
                AddDogView()
                    .presentationDetents([.large])
                    .presentationDragIndicator(.visible)
            }
        }
        .task { await load() }
        .onChange(of: app.selectedDogID) { _, _ in
            Task { await load() }
        }
    }

    private func populatedContent(_ insights: InsightsSummary) -> some View {
        if insights.totalAnalyses == 0 {
            return AnyView(
                EmptyStateView(
                    icon: "chart.bar.xaxis",
                    title: "No patterns yet",
                    message: "Record a sound or analyze a video with \(app.selectedDog?.name ?? "your dog") to start spotting behavior patterns.",
                    actionTitle: "Analyze a Sound",
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
                VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                    heroCard(insights)
                    if insights.isInsufficientData && insights.totalAnalyses > 0 {
                        insufficientCard(insights)
                    }
                    statsGrid(insights)
                    if !insights.stateDistribution.isEmpty {
                        distributionSection(
                            title: "Estimated states",
                            rows: insights.stateDistribution.map {
                                DistributionDatum($0.state.shortName, $0.count, $0.state.accentColor)
                            },
                            footer: "How often each estimated state shows up across analyses."
                        )
                    }
                    if !insights.timeOfDayDistribution.isEmpty {
                        distributionSection(
                            title: "Time of day",
                            rows: insights.timeOfDayDistribution.map {
                                DistributionDatum($0.bucket.displayName, $0.count, BarklyColor.info)
                            },
                            footer: "When BARKLY analyses tend to happen with this dog."
                        )
                    }
                }
                .padding(.horizontal, BarklySpacing.pagePadding)
                .padding(.top, BarklySpacing.sm)
                .padding(.bottom, BarklySpacing.xl)
            }
            .accessibilityIdentifier("insights_content")
        )
    }

    private func heroCard(_ insights: InsightsSummary) -> some View {
        let dog = app.dogs.first { $0.id == insights.dogID }
        return BarklyCard {
            VStack(alignment: .leading, spacing: BarklySpacing.sm) {
                Text("\(dog?.name ?? "Your dog")'s behavior patterns")
                    .font(BarklyFont.cardTitle)
                    .foregroundStyle(BarklyColor.primaryText)
                Text(insights.trendMessage)
                    .font(BarklyFont.body)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .accessibilityIdentifier("insights_hero")
    }

    private func insufficientCard(_ insights: InsightsSummary) -> some View {
        HStack(alignment: .top, spacing: BarklySpacing.md) {
            Image(systemName: "hourglass")
                .font(.system(size: 20, weight: .semibold))
                .foregroundStyle(BarklyColor.warning)
                .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: BarklySpacing.xs) {
                Text("Not enough data yet")
                    .font(BarklyFont.label)
                    .foregroundStyle(BarklyColor.primaryText)
                Text("\(insights.usableAnalyses) of \(InsightsSummary.minimumAnalysesForPatterns) completed analyses. The counts below are real, but they are too few to call a pattern.")
                    .font(BarklyFont.caption)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 0)
        }
        .padding(BarklySpacing.cardPadding)
        .background(BarklyColor.cosmicOrangeSoft, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
        .accessibilityElement(children: .combine)
        .accessibilityIdentifier("insights_insufficient")
    }

    private func statsGrid(_ insights: InsightsSummary) -> some View {
        LazyVGrid(
            columns: [GridItem(.flexible(), spacing: BarklySpacing.md), GridItem(.flexible(), spacing: BarklySpacing.md)],
            spacing: BarklySpacing.md
        ) {
            InsightStatCard(
                label: "Most common vocalization",
                value: insights.mostCommonVocalization?.displayName ?? "—"
            )
            InsightStatCard(
                label: "Most frequent state",
                value: insights.mostFrequentState?.shortName ?? "—"
            )
            InsightStatCard(
                label: "Most active time",
                value: insights.mostActiveTime?.displayName ?? "—"
            )
            InsightStatCard(
                label: "Completed analyses",
                value: "\(insights.usableAnalyses)"
            )
        }
    }

    private func distributionSection(
        title: String,
        rows: [DistributionDatum],
        footer: String
    ) -> some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            SectionHeader(title: title, subtitle: footer)
            if let maxCount = rows.map(\.count).max(), maxCount > 0 {
                VStack(spacing: BarklySpacing.sm) {
                    ForEach(rows) { row in
                        DistributionBar(label: row.label, count: row.count, maxCount: maxCount, tint: row.tint)
                    }
                }
                .padding(BarklySpacing.cardPadding)
                .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                        .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
                )
            }
        }
    }

    private func load() async {
        guard let dog = app.selectedDog else { return }
        state = .loading
        do {
            let insights = try await app.insightsRepository.fetchInsights(for: dog.id)
            state = .loaded(insights)
        } catch {
            let failure = ErrorMapper.failure(for: error)
            state = ErrorMapper.isOffline(error) ? .offline(failure) : .failed(failure)
        }
    }
}

private struct DistributionDatum: Identifiable {
    let id = UUID()
    let label: String
    let count: Int
    let tint: Color

    init(_ label: String, _ count: Int, _ tint: Color) {
        self.label = label
        self.count = count
        self.tint = tint
    }
}

private struct InsightStatCard: View {
    let label: String
    let value: String

    var body: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.xs) {
            Text(label)
                .font(BarklyFont.caption)
                .foregroundStyle(BarklyColor.secondaryText)
                .lineLimit(2)
                .fixedSize(horizontal: false, vertical: true)
            Text(value)
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundStyle(BarklyColor.primaryText)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(BarklySpacing.md)
        .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
        )
        .accessibilityElement(children: .combine)
    }
}

private struct DistributionBar: View {
    let label: String
    let count: Int
    let maxCount: Int
    let tint: Color

    var body: some View {
        HStack(spacing: BarklySpacing.md) {
            Text(label)
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.primaryText)
                .frame(width: 98, alignment: .leading)
                .lineLimit(1)
                .minimumScaleFactor(0.8)
            GeometryReader { proxy in
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(BarklyColor.surface)
                    Capsule()
                        .fill(tint)
                        .frame(width: proxy.size.width * ratio)
                }
            }
            .frame(height: 12)
            Text("\(count)")
                .font(.system(size: 15, weight: .semibold, design: .rounded))
                .foregroundStyle(BarklyColor.secondaryText)
                .frame(width: 28, alignment: .trailing)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(label), \(count) analyses")
    }

    private var ratio: CGFloat {
        guard maxCount > 0 else { return 0 }
        return CGFloat(count) / CGFloat(maxCount)
    }
}

#Preview("Insights") {
    InsightsView()
        .environment(AppContainer())
}