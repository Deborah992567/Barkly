import SwiftUI

struct AuthView: View {
    @Environment(AppContainer.self) private var app

    private enum Mode {
        case login
        case signUp
    }

    @State private var mode: Mode = .login
    @State private var email = ""
    @State private var password = ""
    @State private var displayName = ""
    @State private var errorMessage: String?
    @State private var isBusy = false
    @FocusState private var focusedField: Field?

    private enum Field {
        case email
        case password
        case name
    }

    var body: some View {
        ZStack {
            BarklyColor.background
                .ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(spacing: BarklySpacing.lg) {
                    header

                    card

                    submitButton

                    switchButton
                }
                .frame(maxWidth: 440)
                .padding(.horizontal, BarklySpacing.pagePadding)
                .padding(.top, BarklySpacing.xl)
            }
        }
        .scrollDismissesKeyboard(.interactively)
    }

    private var header: some View {
        VStack(spacing: BarklySpacing.sm) {
            Text("BARKLY")
                .font(BarklyFont.brand)
                .tracking(1.5)
                .foregroundStyle(BarklyColor.primaryText)
            Text(mode == .login ? "Welcome back" : "Create your account")
                .font(BarklyFont.heroTitle)
                .foregroundStyle(BarklyColor.primaryText)
            Text("Your analyses sync to your BARKLY account across devices.")
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.secondaryText)
                .multilineTextAlignment(.center)
        }
    }

    private var card: some View {
        VStack(spacing: BarklySpacing.md) {
            if mode == .signUp {
                BarklyTextField(
                    "Your name (optional)",
                    text: $displayName,
                    icon: "person.fill"
                )
                .focused($focusedField, equals: .name)
                .textContentType(.name)
                .submitLabel(.next)
                .onSubmit { focusedField = .email }
            }

            BarklyTextField(
                "Email",
                text: $email,
                icon: "envelope.fill"
            )
            .focused($focusedField, equals: .email)
            .keyboardType(.emailAddress)
            .textContentType(.emailAddress)
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .submitLabel(.next)
            .onSubmit { focusedField = .password }

            BarklyTextField(
                "Password",
                text: $password,
                icon: "lock.fill",
                isSecure: true
            )
            .focused($focusedField, equals: .password)
            .textContentType(mode == .login ? .password : .newPassword)
            .submitLabel(.go)
            .onSubmit { submit() }

            if let errorMessage {
                Text(errorMessage)
                    .font(BarklyFont.caption)
                    .foregroundStyle(BarklyColor.error)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(BarklySpacing.lg)
        .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
        )
    }

    private var submitButton: some View {
        BarklyButton(
            title: mode == .login ? "Sign In" : "Create Account",
            icon: "arrow.right",
            isLoading: isBusy
        ) {
            submit()
        }
        .accessibilityIdentifier("auth_submit")
    }

    private var switchButton: some View {
        Button {
            Haptics.light()
            withAnimation(.easeInOut(duration: 0.2)) {
                mode = (mode == .login) ? .signUp : .login
            }
            errorMessage = nil
        } label: {
            Text(mode == .login ? "New to BARKLY? Create an account" : "Already have an account? Sign in")
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                .frame(minHeight: 44)
        }
        .accessibilityHint("Switches between signing in and creating an account")
    }

    private func submit() {
        guard let normalized = normalizedEmail else { return }
        guard password.count >= 8 else {
            errorMessage = "Password must be at least 8 characters."
            return
        }
        errorMessage = nil
        isBusy = true
        Task {
            defer { isBusy = false }
            do {
                switch mode {
                case .login:
                    try await app.authService.login(email: normalized, password: password)
                case .signUp:
                    try await app.authService.register(
                        email: normalized,
                        password: password,
                        displayName: displayName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : displayName
                    )
                }
                await app.loadDogs()
            } catch let error as AuthenticationError {
                errorMessage = error.errorDescription
            } catch {
                errorMessage = "Something went wrong. Please try again."
            }
        }
    }

    private var normalizedEmail: String? {
        let trimmed = email.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !trimmed.isEmpty, trimmed.contains("@") else {
            errorMessage = "Enter a valid email address."
            return nil
        }
        return trimmed
    }
}

struct BarklyTextField: View {
    private let title: String
    @Binding private var text: String
    private let icon: String
    private let isSecure: Bool

    init(_ title: String, text: Binding<String>, icon: String, isSecure: Bool = false) {
        self.title = title
        _text = text
        self.icon = icon
        self.isSecure = isSecure
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 15, weight: .medium))
                .foregroundStyle(BarklyColor.secondaryText)
                .frame(width: 22)
            Group {
                if isSecure {
                    SecureField(title, text: $text)
                } else {
                    TextField(title, text: $text)
                }
            }
            .font(BarklyFont.body)
            .foregroundStyle(BarklyColor.primaryText)
        }
        .padding(.horizontal, 14)
        .frame(minHeight: 50)
        .background(BarklyColor.surface, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .strokeBorder(BarklyColor.divider.opacity(0.7), lineWidth: 1)
        )
    }
}

private extension View {
    func accessibleCopy() -> some View {
        self
    }
}

#Preview {
    AuthView()
        .environment(AppContainer())
}