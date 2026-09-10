import SwiftUI

struct AnalyzeView: View {
    enum Route: Hashable {
        case record
        case video
        case upload
    }

    @Environment(AppContainer.self) private var app
    @State private var path: [Route] = []

    var body: some View {
        NavigationStack(path: $path) {
            AnalyzeOptionsView()
                .navigationDestination(for: Route.self) { route in
                    destination(for: route)
                }
        }
        .onAppear {
            consumePendingPath()
        }
        .onChange(of: app.pendingAnalysisPath) { _, newValue in
            guard let newValue else { return }
            app.pendingAnalysisPath = nil
            path = [Route(newValue)]
        }
    }

    private func consumePendingPath() {
        guard let pending = app.pendingAnalysisPath else { return }
        app.pendingAnalysisPath = nil
        path = [Route(pending)]
    }

    @ViewBuilder
    private func destination(for route: Route) -> some View {
        switch route {
        case .record:
            RecordSoundFlowView(onDone: { path.removeAll() })
        case .video:
            MediaFlowView(mode: .video, onDone: { path.removeAll() })
        case .upload:
            MediaFlowView(mode: .any, onDone: { path.removeAll() })
        }
    }
}

private extension AnalyzeView.Route {
    init(_ path: AnalysisPath) {
        switch path {
        case .record: self = .record
        case .video: self = .video
        case .upload: self = .upload
        }
    }
}

struct AnalyzeOptionsView: View {
    @Environment(AppContainer.self) private var app

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                header
                primaryCard
                pathwayList
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.top, BarklySpacing.sm)
            .padding(.bottom, BarklySpacing.xl)
        }
        .background(BarklyColor.background.ignoresSafeArea())
        .navigationTitle("Analyze")
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(BarklyColor.background, for: .navigationBar)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.sm) {
            Text("What should we listen to?")
                .font(BarklyFont.heroTitle)
                .foregroundStyle(BarklyColor.primaryText)
            Text("Pick an input. BARKLY estimates what your dog may be communicating from observable signals.")
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.secondaryText)
        }
    }

    private var primaryCard: some View {
        BarklyCard {
            VStack(alignment: .leading, spacing: BarklySpacing.md) {
                Text("Record a sound")
                    .font(BarklyFont.cardTitle)
                    .foregroundStyle(BarklyColor.primaryText)
                Text("Capture a bark, whine, growl, or howl in the moment.")
                    .font(BarklyFont.subheadline)
                    .foregroundStyle(BarklyColor.secondaryText)
                BarklyButton(title: "Start Recording", icon: "mic.fill") {
                    app.openAnalyzer(.record)
                }
            }
        }
    }

    private var pathwayList: some View {
        VStack(spacing: BarklySpacing.md) {
            PathwayRow(
                icon: "video.fill",
                title: "Analyze a video",
                subtitle: "Choose a video clip of your dog's behavior."
            ) {
                app.openAnalyzer(.video)
            }
            PathwayRow(
                icon: "photo.fill",
                title: "Upload media",
                subtitle: "Pick a photo or video you already have."
            ) {
                app.openAnalyzer(.upload)
            }
        }
    }
}

private struct PathwayRow: View {
    let icon: String
    let title: String
    let subtitle: String
    let action: () -> Void

    var body: some View {
        Button(action: {
            Haptics.light()
            action()
        }) {
            HStack(spacing: BarklySpacing.md) {
                ZStack {
                    RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous)
                        .fill(BarklyColor.cosmicOrangeSoft)
                        .frame(width: 46, height: 46)
                    Image(systemName: icon)
                        .font(.system(size: 19, weight: .semibold))
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                }
                .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(BarklyFont.label)
                        .foregroundStyle(BarklyColor.primaryText)
                    Text(subtitle)
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.secondaryText)
                }
                Spacer(minLength: 0)
                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(BarklyColor.tertiaryText)
                    .accessibilityHidden(true)
            }
            .padding(BarklySpacing.md)
            .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                    .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
            )
            .contentShape(RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
        }
        .buttonStyle(BarklyRowPressStyle())
        .accessibilityElement(children: .combine)
        .accessibilityHint(subtitle)
    }
}

struct BarklyRowPressStyle: ButtonStyle {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(reduceMotion ? 1 : (configuration.isPressed ? 0.985 : 1))
            .opacity(configuration.isPressed ? 0.9 : 1)
    }
}

#Preview {
    NavigationStack {
        AnalyzeOptionsView()
    }
    .environment(AppContainer())
}