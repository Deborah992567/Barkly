import SwiftUI

struct DogDetailView: View {
    @Environment(AppContainer.self) private var app

    private let dog: Dog

    @State private var draftName: String
    @State private var draftBreed: String
    @State private var draftNotes: String
    @State private var saved = false

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
                    SectionHeader(title: "Details", subtitle: "Profile changes stay on this device for now.")

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
                }

                BarklyButton(title: "Save Changes") {
                    save()
                }

                if saved {
                    Text("Saved")
                        .font(BarklyFont.label)
                        .foregroundStyle(BarklyColor.success)
                        .frame(maxWidth: .infinity)
                }
            }
            .padding(.horizontal, BarklySpacing.pagePadding)
            .padding(.top, BarklySpacing.sm)
            .padding(.bottom, BarklySpacing.xl)
        }
        .background(BarklyColor.background.ignoresSafeArea())
        .navigationTitle(dog.name)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var headerCard: some View {
        BarklyCard {
            HStack(spacing: BarklySpacing.md) {
                DogAvatar(dog: dog, size: 72)
                VStack(alignment: .leading, spacing: 2) {
                    Text(dog.name)
                        .font(BarklyFont.displayHeading)
                        .foregroundStyle(BarklyColor.primaryText)
                    Text("\(dog.breed) \u{00B7} \(dog.ageDescription)")
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
        }
        .padding(.vertical, BarklySpacing.md)
    }

    private func save() {
        guard !draftName.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        var updated = dog
        updated.name = draftName.trimmingCharacters(in: .whitespaces)
        updated.breed = draftBreed.trimmingCharacters(in: .whitespaces)
        updated.notes = draftNotes.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : draftNotes
        Haptics.success()
        Task {
            await app.updateDog(updated)
        }
        withAnimation(.easeOut(duration: 0.2)) {
            saved = true
        }
    }
}

#Preview {
    NavigationStack {
        DogDetailView(dog: MockSeeds.max)
    }
    .environment(AppContainer())
}