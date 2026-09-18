import SwiftUI

struct RootView: View {
    @Environment(AppContainer.self) private var app
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        Group {
            if !app.hasCompletedOnboarding {
                WelcomeView()
            } else if app.usesBackend && !app.authService.isAuthenticated {
                AuthView()
            } else {
                AppTabView()
            }
        }
        .transition(.opacity.combined(with: .scale(scale: 0.985)))
        .animation(reduceMotion ? nil : .easeInOut(duration: 0.32), value: app.hasCompletedOnboarding)
        .animation(reduceMotion ? nil : .easeInOut(duration: 0.32), value: app.authService.isAuthenticated)
        .preferredColorScheme(app.appearanceMode.colorScheme)
    }
}