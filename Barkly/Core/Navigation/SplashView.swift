import SwiftUI

/// Brand splash shown briefly before the onboarding/auth flow. Uses the same
/// visual language as WelcomeView so the launch-to-greeting transition is smooth.
struct SplashView: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    @State private var entrance = false
    @State private var fadeOut = false

    var body: some View {
        ZStack {
            BarklyColor.background
                .ignoresSafeArea()

            VStack(spacing: BarklySpacing.md) {
                BarklyDogHeroView(size: 180)
                    .scaleEffect(entrance ? 1 : 0.88)
                    .opacity(entrance ? 1 : 0)

                VStack(spacing: BarklySpacing.xs) {
                    Text("BARKLY")
                        .font(BarklyFont.brand)
                        .tracking(2)
                        .foregroundStyle(BarklyColor.primaryText)
                    Text("Understand your dog beyond the bark.")
                        .font(BarklyFont.body)
                        .foregroundStyle(BarklyColor.secondaryText)
                }
                .opacity(entrance ? 1 : 0)
            }
        }
        .opacity(fadeOut ? 0 : 1)
        .onAppear {
            guard !reduceMotion else {
                entrance = true
                return
            }
            withAnimation(.spring(response: 0.6, dampingFraction: 0.7)) {
                entrance = true
            }
        }
    }

    /// Fades the splash out; call before swapping it for the real root content.
    func beginExit() {
        withAnimation(.easeOut(duration: 0.35)) {
            fadeOut = true
        }
    }
}

#Preview("Splash") {
    SplashView()
}