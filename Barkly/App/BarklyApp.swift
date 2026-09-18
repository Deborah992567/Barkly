import SwiftUI

@main
struct BarklyApp: App {
    @State private var container = AppContainer()
    @State private var showSplash = true

    var body: some Scene {
        WindowGroup {
            ZStack {
                if showSplash {
                    SplashView()
                        .transition(.opacity)
                } else {
                    RootView()
                        .transition(.opacity)
                }
            }
            .environment(container)
            .tint(BarklyColor.cosmicOrange)
            .task {
                guard showSplash else { return }
                try? await Task.sleep(for: .seconds(1.6))
                withAnimation(.easeInOut(duration: 0.3)) {
                    showSplash = false
                }
            }
        }
    }
}