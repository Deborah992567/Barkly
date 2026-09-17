import SwiftUI

struct DogDetailView: View {
    @Environment(AppContainer.self) private var app
    @Environment(\.dismiss) private var dismiss

    private let dog: Dog

    @State private var draftName: String
    @State private var draftBreed: String
    @State private var draftNotes: String
    @State private var isSaving = false
    @State private var saved = false
    @State private var saveError: String?

    init(dog: Dog) {
        self.dog = dog
        _draftName = State(initialValue: dog.name)
        _draftBreed = State(initialValue: dog.breed)
        _draftNotes = State(initialValue: dog.notes ?? "")
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: BarklySpacing.sectionGap) {
                headerCard

                VStack(alignment: .leading, spacing: BarklySpacing.md) {
                    SectionHeader(title: "Details", subtitle: "Changes sync to \(app.owner.name.split(separator: " ").first ?? "your") BARKLY account.")

                    VStack(spacing: 0) {
                        detailField(title: "Name", text: $draftName, prompt: "Dog's name")
                        Divider().overlay(BarklyColor.divider)
                        detailField(title: "Breed", text: $draftBreed, prompt: "Breed")
                        Divider().overlay(BarklyColor.divider)
                        detailField(title: "Notes", text: $draftNotes, prompt: "Anything about your dog")
                    }
                    .padding(.horizontal, BarklySpacing.md)
                    .background(BarklyColor.elevatedSurface, in: RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: BarklyRadius.card, style: .continuous)
                            .strokeBorder(BarklyColor.divider.opacity(0.6), lineWidth: 1)
                    )

                    if let saveError {
                        Label(saveError, systemImage: "exclamationmark.triangle.fill")
                            .font(BarklyFont.caption)
                            .foregroundStyle(BarklyColor.error)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .accessibilityIdentifier("dog_edit_error")
                    }
                }

                BarklyButton(title: "Save Changes", icon: "checkmark", isLoading: isSaving) {
                    save()
                }
                .accessibilityIdentifier("dog_edit_save")

                if saved {
                    Label("Changes saved.", systemImage: "checkmark.circle.fill")
                        .font(BarklyFont.body)
                        .foregroundStyle(BarklyColor.secondaryText)
                        .frame(maxWidth: .infinity)
                        .accessibilityIdentifier("dog_edit_saved")
                }
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.top, BarklySpacing.sm)
            .padding(.bottom, BarklySpacing.xl)
        }
        .background(BarklyColor.background.ignoresSafeArea())
        .navigationTitle(dog.name)
        .navigationBarTitleDisplayMode(.inline)
        .scrollDismissesKeyboard(.interactively)
    }

    private var headerCard: some View {
        BarklyCard {
            HStack(spacing: BarklySpacing.md) {
                DogAvatar(dog: dog, size: 72)
                VStack(alignment: .leading, spacing: 2) {
                    Text(dog.name)
                        .font(BarklyFont.displayHeading)
                        .foregroundStyle(BarklyColor.primaryText)
                    Text("\(dog.breed.isEmpty ? "No breed set" : dog.breed) \u{00B7} \(dog.ageDescription)")
                        .font(BarklyFont.subheadline)
                        .foregroundStyle(BarklyColor.secondaryText)
                }
                Spacer(minLength: 0)
            }
        }
    }

    private func detailField(title: String, text: Binding<String>, prompt: String) -> some View {
        HStack {
            Text(title)
                .font(BarklyFont.label)
                .foregroundStyle(BarklyColor.secondaryText)
                .frame(width: 84, alignment: .leading)
            TextField(prompt, text: text)
                .font(BarklyFont.body)
                .foregroundStyle(BarklyColor.primaryText)
                .textInputAutocapitalization(.words)
                .accessibilityLabel(title)
        }
        .padding(.vertical, BarklySpacing.md)
    }

    private func save() {
        let trimmedName = draftName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedName.isEmpty else {
            saveError = "Give your dog a name before saving."
            return
        }
        saveError = nil
        saved = false
        isSaving = true

        var updated = dog
        updated.name = trimmedName
        updated.breed = draftBreed.trimmingCharacters(in: .whitespacesAndNewlines)
        updated.notes = draftNotes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : draftNotes

        Task {
            defer { isSaving = false }
            do {
                _ = try await app.updateDog(updated)
                Haptics.success()
                withAnimation(.easeOut(duration: 0.2)) {
                    saved = true
                }
            } catch {
                let failure = ErrorMapper.failure(for: error)
                saveError = ErrorMapper.isOffline(error)
                    ? "You're offline. Your changes weren't saved — check your connection and try again."
                    : failure.message
            }
        }
    }
}

#Preview {
    NavigationStack {
        DogDetailView(dog: MockSeeds.max)
    }
    .environment(AppContainer(dependencies: .demo))
}