import SwiftUI

struct HomeView: View {
    @Environment(AppContainer.self) private var app
    @State private var showDogSwitcher = false
    @State private var showAddDog = false

    private var dog: Dog? { app.selectedDog }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                    header
                    if let dog {
                        dogSection(dog)
                        primaryAnalysisCard(dog)
                    } else {
                        EmptyStateView(
                            icon: "pawprint",
                            title: "No dog added yet",
                            message: "Add a dog to start understanding their signals.",
                            actionTitle: "Add Your Dog",
                            action: {
                                Haptics.light()
                                showAddDog = true
                            }
                        )
                        .frame(maxWidth: .infinity)
                        .padding(.top, BarklySpacing.xl)
                    }
                    quickPaths
                }
                .padding(.horizontal, BarklySpacing.pagePadding)
                .padding(.top, BarklySpacing.sm)
                .padding(.bottom, BarklySpacing.xl)
            }
            .background(BarklyColor.background.ignoresSafeArea())
            .navigationBarHidden(true)
            .sheet(isPresented: $showDogSwitcher) {
                DogSelectorView()
                    .presentationDetents([.medium, .large])
                    .presentationDragIndicator(.visible)
            }
            .sheet(isPresented: $showAddDog) {
                AddDogView()
                    .presentationDetents([.large])
                    .presentationDragIndicator(.visible)
            }
        }
    }

    private var header: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 2) {
                Text("\(TimeGreeting.greeting()), \(app.owner.name.split(separator: " ").first ?? "friend")")
                    .font(BarklyFont.heroTitle)
                    .foregroundStyle(BarklyColor.primaryText)
                    .accessibilityAddTraits(.isHeader)
                Text(Date.now.formatted(.dateTime.weekday(.wide).month(.wide).day()))
                    .font(BarklyFont.subheadline)
                    .foregroundStyle(BarklyColor.secondaryText)
            }
            Spacer(minLength: BarklySpacing.sm)
            Button {
                Haptics.light()
                app.openTab(.profile)
            } label: {
                ZStack {
                    Circle()
                        .fill(BarklyColor.cosmicOrangeSoft)
                        .frame(width: 44, height: 44)
                    Image(systemName: "person.fill")
                        .font(.system(size: 17, weight: .medium))
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                }
                .accessibilityHidden(true)
            }
            .accessibilityLabel("Open profile")
            .ensureTouchTarget()
        }
    }

    private func dogSection(_ dog: Dog) -> some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            SectionHeader(title: "Your dog")
            DogProfileHeader(dog: dog) {
                Haptics.light()
                showDogSwitcher = true
            }
            .padding(BarklySpacing.md)
            .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                    .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
            )
        }
    }

    private func primaryAnalysisCard(_ dog: Dog) -> some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            SectionHeader(title: "Start here")
            BarklyCard {
                VStack(alignment: .leading, spacing: BarklySpacing.md) {
                    VStack(alignment: .leading, spacing: BarklySpacing.xs) {
                        Text("How is \(dog.name) feeling?")
                            .font(BarklyFont.displayHeading)
                            .foregroundStyle(BarklyColor.primaryText)
                        Text("Analyze a sound, video, or behavior to get BARKLY's interpretation.")
                            .font(BarklyFont.body)
                            .foregroundStyle(BarklyColor.secondaryText)
                    }
                    BarklyButton(title: "Analyze Your Dog", icon: "waveform") {
                        app.openAnalyzer(.record)
                    }
                    .accessibilityIdentifier("home_analyze_cta")
                }
            }
        }
    }

    private var quickPaths: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            SectionHeader(title: "Or pick an input")
            VStack(spacing: BarklySpacing.md) {
                HomePathRow(icon: "mic.fill", title: "Record a sound", subtitle: "Bark, whine, growl, howl") {
                    app.openAnalyzer(.record)
                }
                HomePathRow(icon: "video.fill", title: "Analyze a video", subtitle: "Behavior caught on video") {
                    app.openAnalyzer(.video)
                }
                HomePathRow(icon: "photo.fill", title: "Upload media", subtitle: "A photo or clip you already have") {
                    app.openAnalyzer(.upload)
                }
            }
        }
    }
}

private struct HomePathRow: View {
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
                        .frame(width: 44, height: 44)
                    Image(systemName: icon)
                        .font(.system(size: 18, weight: .semibold))
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

#Preview("Home") {
    HomeView()
        .environment(AppContainer())
}