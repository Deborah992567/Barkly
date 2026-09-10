import SwiftUI
import UIKit

struct LoadingStateView: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var pulse = false

    var body: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.md) {
            ForEach(0..<3, id: \.self) { _ in
                skeletonRow()
            }
        }
        .padding(.horizontal, BarklySpacing.pagePadding)
        .frame(maxWidth: .infinity, alignment: .leading)
        .opacity(reduceMotion ? 1 : (pulse ? 0.65 : 1))
        .animation(reduceMotion ? nil : .easeInOut(duration: 0.9).repeatForever(autoreverses: true), value: pulse)
        .onAppear { pulse = true }
        .accessibilityLabel("Loading")
        .accessibilityIdentifier("loading_state")
    }

    private func skeletonRow() -> some View {
        HStack(spacing: BarklySpacing.md) {
            RoundedRectangle(cornerRadius: BarklyRadius.small, style: .continuous)
                .fill(BarklyColor.disabled.opacity(0.6))
                .frame(width: 48, height: 48)
            VStack(alignment: .leading, spacing: BarklySpacing.sm) {
                RoundedRectangle(cornerRadius: 4, style: .continuous)
                    .fill(BarklyColor.disabled.opacity(0.6))
                    .frame(maxWidth: 210, minHeight: 14, alignment: .leading)
                    .frame(maxWidth: .infinity, alignment: .leading)
                RoundedRectangle(cornerRadius: 4, style: .continuous)
                    .fill(BarklyColor.disabled.opacity(0.4))
                    .frame(maxWidth: 150, minHeight: 11, alignment: .leading)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }
}

struct EmptyStateView: View {
    var icon: String = "clock"
    var title: String = "Nothing here yet"
    var message: String = "New entries will appear here."
    var actionTitle: String? = nil
    var action: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: BarklySpacing.md) {
            ZStack {
                Circle()
                    .fill(BarklyColor.cosmicOrangeSoft)
                    .frame(width: 76, height: 76)
                Image(systemName: icon)
                    .font(.system(size: 28, weight: .medium))
                    .foregroundStyle(BarklyColor.cosmicOrangeDeep)
            }
            .accessibilityHidden(true)
            Text(title)
                .font(BarklyFont.heroTitle)
                .foregroundStyle(BarklyColor.primaryText)
                .multilineTextAlignment(.center)
            Text(message)
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.secondaryText)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 320)
            if let actionTitle, let action {
                BarklyButton(title: actionTitle, style: .tinted, action: action)
                    .frame(maxWidth: 220)
                    .padding(.top, BarklySpacing.xs)
            }
        }
        .padding(BarklySpacing.xl)
        .accessibilityElement(children: .combine)
    }
}

struct ErrorStateView: View {
    let failure: AppFailure
    var onRetry: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: BarklySpacing.md) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 34, weight: .medium))
                .foregroundStyle(BarklyColor.error)
                .accessibilityHidden(true)
            Text(failure.title)
                .font(BarklyFont.heroTitle)
                .foregroundStyle(BarklyColor.primaryText)
                .multilineTextAlignment(.center)
            Text(failure.message)
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.secondaryText)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 320)
            if let recovery = failure.recovery {
                recoveryButton(recovery)
            }
        }
        .padding(BarklySpacing.xl)
        .accessibilityElement(children: .combine)
    }

    @ViewBuilder
    private func recoveryButton(_ recovery: AppFailure.Recovery) -> some View {
        switch recovery {
        case .retry:
            BarklyButton(title: "Try Again", style: .primary) {
                Haptics.light()
                onRetry?()
            }
            .frame(maxWidth: 240)
            .padding(.top, BarklySpacing.xs)
        case .openSettings:
            BarklyButton(title: "Open Settings", style: .tinted) {
                Haptics.light()
                openSettings()
            }
            .frame(maxWidth: 240)
            .padding(.top, BarklySpacing.xs)
        }
    }

    private func openSettings() {
        guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
        UIApplication.shared.open(url)
    }
}

struct OfflineStateView: View {
    let failure: AppFailure
    var onRetry: (() -> Void)? = nil

    var body: some View {
        VStack(spacing: BarklySpacing.md) {
            Image(systemName: "wifi.slash")
                .font(.system(size: 34, weight: .medium))
                .foregroundStyle(BarklyColor.info)
                .accessibilityHidden(true)
            Text(failure.title)
                .font(BarklyFont.heroTitle)
                .foregroundStyle(BarklyColor.primaryText)
                .multilineTextAlignment(.center)
            Text(failure.message)
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.secondaryText)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 320)
            if let hint = failure.hint {
                Text(hint)
                    .font(BarklyFont.caption)
                    .foregroundStyle(BarklyColor.tertiaryText)
                    .multilineTextAlignment(.center)
            }
            if let onRetry {
                BarklyButton(title: "Try Again", style: .tinted) {
                    Haptics.light()
                    onRetry()
                }
                .frame(maxWidth: 240)
                .padding(.top, BarklySpacing.xs)
            }
        }
        .padding(BarklySpacing.xl)
        .accessibilityElement(children: .combine)
    }
}