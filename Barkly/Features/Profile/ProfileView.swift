import SwiftUI

struct ProfileView: View {
    @Environment(AppContainer.self) private var app
    @State private var showAddDog = false
    @State private var confirmLogOut = false
    @State private var isSigningOut = false

    private let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                    ownerCard

                    dogsSection

                    settingsSection

                    if app.usesBackend {
                        signOutSection
                    }

                    footer
                }
                .padding(.horizontal, BarklySpacing.pagePadding)
                .padding(.top, BarklySpacing.sm)
                .padding(.bottom, BarklySpacing.xl)
            }
            .background(BarklyColor.background.ignoresSafeArea())
            .navigationTitle("Profile")
            .navigationBarTitleDisplayMode(.large)
        }
    }

    private var ownerCard: some View {
        BarklyCard {
            HStack(spacing: BarklySpacing.md) {
                ZStack {
                    Circle()
                        .fill(BarklyColor.cosmicOrangeSoft)
                        .frame(width: 64, height: 64)
                    Text(app.owner.initials)
                        .font(.system(size: 22, weight: .bold, design: .rounded))
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                }
                .accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 2) {
                    Text(app.owner.name)
                        .font(BarklyFont.cardTitle)
                        .foregroundStyle(BarklyColor.primaryText)
                    Text(app.owner.email)
                        .font(BarklyFont.subheadline)
                        .foregroundStyle(BarklyColor.secondaryText)
                    Text("Member since \(app.owner.memberSince.formatted(.dateTime.month().year()))")
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.tertiaryText)
                }
                Spacer(minLength: 0)
            }
        }
        .accessibilityElement(children: .combine)
    }

    private var dogsSection: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            SectionHeader(title: "Your dogs")
            if app.dogs.isEmpty {
                EmptyStateView(
                    icon: "pawprint",
                    title: "No dogs added yet",
                    message: "Add a dog to get started with your first analysis.",
                    actionTitle: "Add Your Dog",
                    action: {
                        Haptics.light()
                        showAddDog = true
                    }
                )
            } else {
                VStack(spacing: 2) {
                    ForEach(app.dogs) { dog in
                        NavigationLink(value: dog) {
                            SettingsRow(
                                icon: "pawprint.fill",
                                tint: BarklyColor.cosmicOrange,
                                title: dog.name,
                                subtitle: "\(dog.breed.isEmpty ? "No breed set" : dog.breed) \u{00B7} \(dog.ageDescription)"
                            )
                        }
                        .buttonStyle(SettingsNavLinkStyle())
                        if dog != app.dogs.last {
                            Divider().overlay(BarklyColor.divider)
                        }
                    }
                    Divider().overlay(BarklyColor.divider)
                    Button {
                        Haptics.light()
                        showAddDog = true
                    } label: {
                        SettingsRow(
                            icon: "plus",
                            tint: BarklyColor.cosmicOrange,
                            title: "Add a dog",
                            subtitle: "Keep signals separate per dog"
                        )
                    }
                    .buttonStyle(SettingsNavLinkStyle())
                }
                .padding(.horizontal, BarklySpacing.md)
                .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                        .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
                )
            }
        }
        .navigationDestination(for: Dog.self) { dog in
            DogDetailView(dog: dog)
        }
        .sheet(isPresented: $showAddDog) {
            AddDogView()
                .presentationDetents([.large])
                .presentationDragIndicator(.visible)
        }
    }

    private var settingsSection: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            SectionHeader(title: "Settings")
            VStack(spacing: 2) {
                NavigationLink {
                    NotificationSettingsView()
                } label: {
                    SettingsRow(icon: "bell.fill", tint: BarklyColor.cosmicOrange, title: "Notifications", subtitle: "New insights and reminders")
                }
                .buttonStyle(SettingsNavLinkStyle())
                Divider().overlay(BarklyColor.divider)
                NavigationLink {
                    AppearanceSettingsView()
                } label: {
                    SettingsRow(icon: "moon.fill", tint: BarklyColor.info, title: "Appearance", subtitle: "Light or dark display")
                }
                .buttonStyle(SettingsNavLinkStyle())
                Divider().overlay(BarklyColor.divider)
                NavigationLink {
                    AccessibilitySettingsView()
                } label: {
                    SettingsRow(icon: "accessibility", tint: BarklyColor.info, title: "Accessibility", subtitle: "VoiceOver, Text Size, Motion")
                }
                .buttonStyle(SettingsNavLinkStyle())
                Divider().overlay(BarklyColor.divider)
                NavigationLink {
                    PrivacyView()
                } label: {
                    SettingsRow(icon: "lock.shield.fill", tint: BarklyColor.success, title: "Privacy", subtitle: "How your data is handled")
                }
                .buttonStyle(SettingsNavLinkStyle())
                Divider().overlay(BarklyColor.divider)
                NavigationLink {
                    TermsView()
                } label: {
                    SettingsRow(icon: "doc.text.fill", tint: BarklyColor.info, title: "Terms of Service", subtitle: "Using BARKLY")
                }
                .buttonStyle(SettingsNavLinkStyle())
                Divider().overlay(BarklyColor.divider)
                NavigationLink {
                    AboutView()
                } label: {
                    SettingsRow(icon: "info.circle.fill", tint: BarklyColor.cosmicOrange, title: "About BARKLY", subtitle: "Version \(version)")
                }
                .buttonStyle(SettingsNavLinkStyle())
            }
            .padding(.horizontal, BarklySpacing.md)
            .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                    .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
            )
        }
    }

    private var signOutSection: some View {
        VStack(spacing: BarklySpacing.sm) {
            Button {
                confirmLogOut = true
            } label: {
                HStack(spacing: BarklySpacing.md) {
                    ZStack {
                        RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous)
                            .fill(BarklyColor.error.opacity(0.12))
                            .frame(width: 34, height: 34)
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundStyle(BarklyColor.error)
                    }
                    .accessibilityHidden(true)
                    Text(isSigningOut ? "Signing out…" : "Sign Out")
                        .font(BarklyFont.label)
                        .foregroundStyle(BarklyColor.error)
                    Spacer(minLength: 0)
                    if isSigningOut {
                        ProgressView()
                            .tint(BarklyColor.error)
                    }
                }
                .padding(.horizontal, BarklySpacing.md)
                .padding(.vertical, BarklySpacing.md)
                .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                        .strokeBorder(BarklyColor.error.opacity(0.25), lineWidth: 1)
                )
            }
            .buttonStyle(.plain)
            .disabled(isSigningOut)
            .accessibilityIdentifier("profile_sign_out")
            .confirmationDialog(
                "Sign out of BARKLY?",
                isPresented: $confirmLogOut,
                titleVisibility: .visible
            ) {
                Button("Sign Out", role: .destructive) {
                    signOut()
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Your analyses stay saved. You'll need to sign in again to view them.")
            }
        }
    }

    private func signOut() {
        isSigningOut = true
        Task {
            defer { isSigningOut = false }
            await app.signOut()
        }
    }

    private var footer: some View {
        VStack(spacing: BarklySpacing.sm) {
            Text("BARKLY")
                .font(.system(size: 16, weight: .bold, design: .rounded))
                .foregroundStyle(BarklyColor.secondaryText)
            Text("Behavioral estimates based on observable signals. Not a veterinary diagnostic tool.")
                .font(BarklyFont.caption)
                .foregroundStyle(BarklyColor.tertiaryText)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .accessibilityElement(children: .combine)
    }
}

struct SettingsRow: View {
    let icon: String
    let tint: Color
    let title: String
    var subtitle: String? = nil
    var showsChevron: Bool = true

    var body: some View {
        HStack(spacing: BarklySpacing.md) {
            ZStack {
                RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous)
                    .fill(BarklyColor.cosmicOrangeSoft)
                    .frame(width: 34, height: 34)
                Image(systemName: icon)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(tint)
            }
            .accessibilityHidden(true)
            VStack(alignment: .leading, spacing: 1) {
                Text(title)
                    .font(BarklyFont.label)
                    .foregroundStyle(BarklyColor.primaryText)
                if let subtitle {
                    Text(subtitle)
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.secondaryText)
                }
            }
            Spacer(minLength: 0)
            if showsChevron {
                Image(systemName: "chevron.right")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(BarklyColor.tertiaryText)
                    .accessibilityHidden(true)
            }
        }
        .padding(.vertical, BarklySpacing.md)
        .contentShape(Rectangle())
    }
}

struct SettingsNavLinkStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .background(configuration.isPressed ? BarklyColor.surface : Color.clear)
    }
}

#Preview("Profile") {
    ProfileView()
        .environment(AppContainer())
}