import SwiftUI

struct WelcomeView: View {
    @Environment(AppContainer.self) private var app
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    @State private var entrance = false
    @State private var isCheering = false

    var body: some View {
        ZStack {
            BarklyColor.background
                .ignoresSafeArea()

            pawDecorations

            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    brandBlock
                        .padding(.top, BarklySpacing.xl)

                    BarklyDogHeroView(size: 280)
                        .padding(.top, BarklySpacing.lg)
                        .scaleEffect(isCheering ? 1.05 : 1)
                        .animation(.spring(response: 0.32, dampingFraction: 0.55), value: isCheering)

                    actions
                        .padding(.top, BarklySpacing.xl)
                        .padding(.bottom, BarklySpacing.xl)
                }
                .frame(maxWidth: .infinity)
                .padding(.horizontal, BarklySpacing.pagePadding)
            }
        }
        .opacity(entrance ? 1 : 0)
        .offset(y: entrance ? 0 : 10)
        .onAppear {
            guard !reduceMotion else {
                entrance = true
                return
            }
            withAnimation(.easeOut(duration: 0.5)) {
                entrance = true
            }
        }
    }

    private var brandBlock: some View {
        VStack(spacing: BarklySpacing.sm) {
            Text("BARKLY")
                .font(BarklyFont.brand)
                .tracking(1.5)
                .foregroundStyle(BarklyColor.primaryText)
                .accessibilityAddTraits(.isHeader)
            Text("Understand your dog beyond the bark.")
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.secondaryText)
                .multilineTextAlignment(.center)
        }
    }

    private var actions: some View {
        VStack(spacing: BarklySpacing.sm) {
            BarklyButton(title: "Get Started", icon: "pawprint.fill") {
                Haptics.medium()
                cheer()
            }
            Button {
                Haptics.medium()
                app.completeOnboarding()
            } label: {
                Text("I already have an account")
                    .font(BarklyFont.label)
                    .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                    .frame(minHeight: 44)
                    .frame(maxWidth: .infinity)
            }
            .accessibilityHint("Continues into the app")
        }
        .frame(maxWidth: 420)
    }

    private var pawDecorations: some View {
        ZStack {
            PawDecorationView(corner: .topLeft, size: 118, opacity: 0.9)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            PawDecorationView(corner: .topRight, size: 82, opacity: 0.6)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
                .padding(.top, BarklySpacing.lg)
            PawDecorationView(corner: .bottomLeft, size: 96, opacity: 0.45)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomLeading)
            PawDecorationView(corner: .bottomRight, size: 70, opacity: 0.7)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottomTrailing)
        }
        .allowsHitTesting(false)
        .accessibilityHidden(true)
    }

    private func cheer() {
        withAnimation(.easeOut(duration: 0.2)) {
            isCheering = true
        }
        Task { @MainActor in
            try? await Task.sleep(nanoseconds: 420_000_000)
            withAnimation(.easeInOut(duration: 0.25)) {
                isCheering = false
            }
            app.completeOnboarding()
        }
    }
}

#Preview {
    WelcomeView()
        .environment(AppContainer())
}