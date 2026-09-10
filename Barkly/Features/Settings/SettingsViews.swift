import SwiftUI

struct NotificationSettingsView: View {
    @State private var insightsEnabled = true
    @State private var weeklySummary = true
    @State private var gentleReminders = false

    var body: some View {
        List {
            Section {
                Toggle(isOn: $insightsEnabled) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("New insights")
                            .font(BarklyFont.label)
                        Text("A note when a new pattern is spotted.")
                            .font(BarklyFont.caption)
                            .foregroundStyle(BarklyColor.secondaryText)
                    }
                }
                Toggle(isOn: $weeklySummary) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Weekly summary")
                            .font(BarklyFont.label)
                        Text("A weekly recap of your dog's behavior.")
                            .font(BarklyFont.caption)
                            .foregroundStyle(BarklyColor.secondaryText)
                    }
                }
                Toggle(isOn: $gentleReminders) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Gentle reminders")
                            .font(BarklyFont.label)
                        Text("A nudge to log a behavior now and then.")
                            .font(BarklyFont.caption)
                            .foregroundStyle(BarklyColor.secondaryText)
                    }
                }
            } footer: {
                Text("Notification preferences are saved on this device for now.")
            }
        }
        .navigationTitle("Notifications")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct AppearanceSettingsView: View {
    @Environment(AppContainer.self) private var app

    var body: some View {
        List {
            Section {
                ForEach(AppearanceMode.allCases, id: \.self) { mode in
                    Button {
                        Haptics.light()
                        app.setAppearanceMode(mode)
                    } label: {
                        HStack {
                            Text(mode.displayName)
                                .font(BarklyFont.body)
                                .foregroundStyle(BarklyColor.primaryText)
                            Spacer()
                            if app.appearanceMode == mode {
                                Image(systemName: "checkmark")
                                    .foregroundStyle(BarklyColor.cosmicOrange)
                                    .accessibilityHidden(true)
                            }
                        }
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .accessibilityAddTraits(app.appearanceMode == mode ? [.isSelected] : [])
                }
            } header: {
                Text("Appearance")
            } footer: {
                Text("BARKLY keeps a calm, white-led look in either mode.")
            }
        }
        .navigationTitle("Appearance")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct AccessibilitySettingsView: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize

    private var textSizeDescription: String {
        if dynamicTypeSize < .large {
            return "Smaller than default"
        }
        if dynamicTypeSize > .large {
            return "Larger than default"
        }
        return "Default"
    }

    var body: some View {
        List {
            Section {
                LabeledContent("Reduce Motion", value: reduceMotion ? "On" : "Off")
                LabeledContent("Text Size", value: textSizeDescription)
            } header: {
                Text("Your system settings")
            } footer: {
                Text("BARKLY adapts to these automatically. With Reduce Motion on, breathing, blinking, and decorative animations are minimized.")
            }
            Section {
                Link(destination: accessibilityURL) {
                    SettingsRow(icon: "slider.horizontal.3", tint: BarklyColor.info, title: "Accessibility settings")
                }
                .buttonStyle(SettingsNavLinkStyle())
            } header: {
                Text("More")
            } footer: {
                Text("BARKLY includes VoiceOver labels, Dynamic Type, and visible focus indicators across the app.")
            }
        }
        .navigationTitle("Accessibility")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var accessibilityURL: URL {
        URL(string: UIApplication.openSettingsURLString)!
    }
}

struct PrivacyView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BarklySpacing.md) {
                Text("BARKLY Privacy")
                    .font(BarklyFont.heroTitle)
                    .foregroundStyle(BarklyColor.primaryText)
                legalParagraph("Your media and behavior data belong to you. This placeholder page will describe exactly how BARKLY stores, processes, and shares audio, video, photos, and analysis results once the service is live.")
                legalSection("What we collect", body: "Sound and media you choose to analyze, plus basic profile details you provide. Analysis estimates are generated from observable signals.")
                legalSection("How it's used", body: "To produce behavior estimates, to personalize your history and insights, and to improve the service. We will not sell your data.")
                legalSection("Permissions", body: "Microphone and photo library access are requested only when you choose a recording or media flow — never up front.")
                legalParagraph("This placeholder is structured so final, accurate legal copy can be added before launch.")
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.vertical, BarklySpacing.lg)
        }
        .background(BarklyColor.background.ignoresSafeArea())
        .navigationTitle("Privacy")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func legalSection(_ title: String, body: String) -> some View {
        VStack(alignment: .leading, spacing: BarklySpacing.xs) {
            Text(title)
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.primaryText)
            legalParagraph(body)
        }
    }

    private func legalParagraph(_ text: String) -> some View {
        Text(text)
            .font(BarklyFont.body)
            .foregroundStyle(BarklyColor.secondaryText)
            .fixedSize(horizontal: false, vertical: true)
    }
}

struct TermsView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BarklySpacing.md) {
                Text("Terms of Service")
                    .font(BarklyFont.heroTitle)
                    .foregroundStyle(BarklyColor.primaryText)
                legalParagraph("Placeholder for BARKLY's final Terms of Service. It will cover how the app may be used and clarify that behavior estimates are informational only.")
                legalSection("Estimated insights", body: "BARKLY estimates what a dog may be communicating from observable signals. Estimates are not statements of fact.")
                legalSection("Not medical advice", body: "BARKLY does not provide veterinary or medical diagnosis. For health concerns, consult a qualified veterinarian.")
                legalSection("Your content", body: "You keep ownership of the media you provide. You control how it is used within the app.")
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.vertical, BarklySpacing.lg)
        }
        .background(BarklyColor.background.ignoresSafeArea())
        .navigationTitle("Terms of Service")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func legalSection(_ title: String, body: String) -> some View {
        VStack(alignment: .leading, spacing: BarklySpacing.xs) {
            Text(title)
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.primaryText)
            legalParagraph(body)
        }
    }

    private func legalParagraph(_ text: String) -> some View {
        Text(text)
            .font(BarklyFont.body)
            .foregroundStyle(BarklyColor.secondaryText)
            .fixedSize(horizontal: false, vertical: true)
    }
}

struct AboutView: View {
    private let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
    private let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"

    var body: some View {
        ScrollView {
            VStack(spacing: BarklySpacing.lg) {
                Spacer(minLength: 8)
                Text("BARKLY")
                    .font(BarklyFont.brand)
                    .tracking(1.5)
                    .foregroundStyle(BarklyColor.primaryText)
                Text("Understand your dog beyond the bark.")
                    .font(BarklyFont.body)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .multilineTextAlignment(.center)

                BarklyDogHeroView(size: 170)

                VStack(spacing: BarklySpacing.xs) {
                    Text("Version \(version) (\(build))")
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.tertiaryText)
                    Text("Phase 1 \u{00B7} Frontend foundation")
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.tertiaryText)
                }

                Text("BARKLY produces behavioral estimates from observable sounds, body language, and context. It doesn't literally translate dog language and doesn't provide veterinary diagnosis.")
                    .font(BarklyFont.footnote)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, BarklySpacing.pagePadding)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .frame(maxWidth: .infinity)
        }
        .background(BarklyColor.background.ignoresSafeArea())
        .navigationTitle("About BARKLY")
        .navigationBarTitleDisplayMode(.inline)
    }
}