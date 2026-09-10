import SwiftUI

struct PermissionExplainerView: View {
    let title: String
    let message: String
    let allowTitle: String
    var onAllow: () async -> Void
    var onNotNow: (() -> Void)? = nil

    @State private var isRequesting = false

    var body: some View {
        VStack(spacing: BarklySpacing.lg) {
            Spacer()
            ZStack {
                Circle()
                    .fill(BarklyColor.cosmicOrangeSoft)
                    .frame(width: 116, height: 116)
                Image(systemName: "mic.fill")
                    .font(.system(size: 42, weight: .medium))
                    .foregroundStyle(BarklyColor.cosmicOrangeDeep)
            }
            .accessibilityHidden(true)

            VStack(spacing: BarklySpacing.sm) {
                Text(title)
                    .font(BarklyFont.heroTitle)
                    .foregroundStyle(BarklyColor.primaryText)
                    .multilineTextAlignment(.center)
                Text(message)
                    .font(BarklyFont.body)
                    .foregroundStyle(BarklyColor.secondaryText)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            Spacer()

            VStack(spacing: BarklySpacing.sm) {
                BarklyButton(title: allowTitle, icon: "lock.fill") {
                    request()
                }
                if let onNotNow {
                    Button {
                        Haptics.light()
                        onNotNow()
                    } label: {
                        Text("Not now")
                            .font(BarklyFont.label)
                            .foregroundStyle(BarklyColor.secondaryText)
                            .frame(minHeight: 44)
                            .frame(maxWidth: .infinity)
                    }
                    .accessibilityHint("Returns without recording")
                }
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.bottom, BarklySpacing.lg)
        }
        .overlay {
            if isRequesting {
                ZStack {
                    BarklyColor.background.opacity(0.7)
                    ProgressView("Requesting access")
                        .font(BarklyFont.label)
                }
                .ignoresSafeArea()
            }
        }
    }

    private func request() {
        guard !isRequesting else { return }
        isRequesting = true
        Task {
            await onAllow()
            isRequesting = false
        }
    }
}

#Preview {
    PermissionExplainerView(
        title: "Record your dog's sound",
        message: "BARKLY uses the microphone so you can capture sounds for estimation.",
        allowTitle: "Enable Microphone",
        onAllow: {}
    )
}