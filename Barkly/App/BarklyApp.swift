import SwiftUI

@main
struct BarklyApp: App {
    @State private var container = AppContainer()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(container)
                .tint(BarklyColor.cosmicOrange)
        }
    }
}