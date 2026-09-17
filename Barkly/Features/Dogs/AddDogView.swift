import SwiftUI

/// Creates a new dog through the live repository. The server response becomes
/// the source of truth: the created dog (and its backend id) is what gets
/// added to the app and selected for analysis.
struct AddDogView: View {
    @Environment(AppContainer.self) private var app
    @Environment(\.dismiss) private var dismiss

    @State private var name = ""
    @State private var breed = ""
    @State private var hasDateOfBirth = false
    @State private var dateOfBirth = Calendar.current.date(byAdding: .year, value: -2, to: Date()) ?? Date()
    @State private var notes = ""
    @State private var isSubmitting = false
    @State private var errorMessage: String?
    @FocusState private var nameFocused: Bool

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                    intro

                    VStack(spacing: 0) {
                        field(title: "Name", value: $name, prompt: "Your dog's name", required: true)
                        Divider().overlay(BarklyColor.divider)
                        field(title: "Breed", value: $breed, prompt: "Breed (optional)")
                        Divider().overlay(BarklyColor.divider)
                        dateOfBirthRow
                        Divider().overlay(BarklyColor.divider)
                        field(title: "Notes", value: $notes, prompt: "Anything about your dog (optional)")
                    }
                    .padding(.horizontal, BarklySpacing.md)
                    .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                            .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
                    )

                    if let errorMessage {
                        Label(errorMessage, systemImage: "exclamationmark.triangle.fill")
                            .font(BarklyFont.caption)
                            .foregroundStyle(BarklyColor.error)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .accessibilityIdentifier("add_dog_error")
                    }

                    BarklyButton(title: "Add Dog", icon: "pawprint.fill", isLoading: isSubmitting) {
                        submit()
                    }
                    .accessibilityIdentifier("add_dog_submit")
                    .padding(.top, BarklySpacing.xs)
                }
                .padding(.horizontal, BarklySpacing.pagePadding)
                .padding(.top, BarklySpacing.md)
                .padding(.bottom, BarklySpacing.xl)
            }
            .background(BarklyColor.background.ignoresSafeArea())
            .scrollDismissesKeyboard(.interactively)
            .navigationTitle("Add your dog")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                    .accessibilityLabel("Cancel adding a dog")
                }
            }
            .onAppear {
                nameFocused = true
            }
            .interactiveDismissDisabled(isSubmitting)
        }
    }

    private var intro: some View {
        VStack(alignment: .leading, spacing: BarklySpacing.sm) {
            Text("BARKLY keeps each dog's signals separate so patterns stay accurate.")
                .font(BarklyFont.subheadline)
                .foregroundStyle(BarklyColor.secondaryText)
        }
    }

    private var dateOfBirthRow: some View {
        HStack {
            Text("Birth date")
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.secondaryText)
                .frame(width: 84, alignment: .leading)
            if hasDateOfBirth {
                DatePicker(
                    "Birth date",
                    selection: $dateOfBirth,
                    in: ...Date(),
                    displayedComponents: .date
                )
                .labelsHidden()
                .datePickerStyle(.compact)
                .accessibilityLabel("Date of birth")
            } else {
                Button("Add birth date") {
                    Haptics.light()
                    hasDateOfBirth = true
                }
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.cosmicOrangeDeep)
            }
        }
        .padding(.vertical, BarklySpacing.md)
    }

    private func field(title: String, value: Binding<String>, prompt: String, required: Bool = false) -> some View {
        HStack {
            Text(title)
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.secondaryText)
                .frame(width: 84, alignment: .leading)
            TextField(prompt, text: value)
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.primaryText)
                .textInputAutocapitalization(.words)
                .accessibilityLabel(title)
                .focused($nameFocused, equals: title == "Name")
        }
        .padding(.vertical, BarklySpacing.md)
    }

    private func submit() {
        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedName.isEmpty else {
            errorMessage = "Give your dog a name first."
            Haptics.warning()
            return
        }
        errorMessage = nil
        isSubmitting = true
        Task {
            defer { isSubmitting = false }
            do {
                _ = try await app.addDog(
                    name: trimmedName,
                    breed: breed,
                    dateOfBirth: hasDateOfBirth ? dateOfBirth : Date(),
                    notes: notes
                )
                Haptics.success()
                dismiss()
            } catch {
                let failure = ErrorMapper.failure(for: error)
                errorMessage = ErrorMapper.isOffline(error)
                    ? "You're offline. Your dog wasn't added — reconnect and try again."
                    : failure.message
            }
        }
    }
}

#Preview("Add dog") {
    AddDogView()
        .environment(AppContainer(dependencies: .demo))
}