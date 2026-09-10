import SwiftUI

struct AppTabView: View {
    @Environment(AppContainer.self) private var app

    var body: some View {
        @Bindable var app = app
        TabView(selection: $app.tabSelection) {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "house")
                }
                .tag(AppTab.home)

            AnalyzeView()
                .tabItem {
                    Label("Analyze", systemImage: "waveform")
                }
                .tag(AppTab.analyze)

            HistoryView()
                .tabItem {
                    Label("History", systemImage: "clock")
                }
                .tag(AppTab.history)

            InsightsView()
                .tabItem {
                    Label("Insights", systemImage: "chart.bar.xaxis")
                }
                .tag(AppTab.insights)

            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.crop.circle")
                }
                .tag(AppTab.profile)
        }
        .tint(BarklyColor.cosmicOrange)
    }
}