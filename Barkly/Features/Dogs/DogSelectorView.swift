import SwiftUI
import UIKit

struct DogSelectorView: View {
    @Environment(AppContainer.self) private var app
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                Section {
                    ForEach(app.dogs) { dog in
                        DogSelectRow(dog: dog, isSelected: dog.id == app.selectedDogID) {
                            Haptics.medium()
                            app.selectDog(id: dog.id)
                            UIAccessibility.post(
                                notification: .announcement,
                                argument: "Now analyzing with \(dog.name)"
                            )
                            dismiss()
                        }
                    }
                } footer: {
                    Text("BARKLY keeps its analysis per dog, so patterns stay accurate.")
                }
            }
            .navigationTitle("Switch Dog")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                    .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                }
            }
        }
        .presentationDragIndicator(.visible)
        .accessibilityIdentifier("dog_selector")
    }
}

private struct DogSelectRow: View {
    let dog: Dog
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: BarklySpacing.md) {
                DogAvatar(dog: dog, size: 52)
                VStack(alignment: .leading, spacing: 2) {
                    Text(dog.name)
                        .font(BarklyFont.label)
                        .foregroundStyle(BarklyColor.primaryText)
                    Text("\(dog.breed) \u{00B7} \(dog.ageDescription)")
                        .font(BarklyFont.caption)
                        .foregroundStyle(BarklyColor.secondaryText)
                }
                Spacer(minLength: 0)
                if isSelected {
                    HStack(spacing: BarklySpacing.xs) {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundStyle(BarklyColor.cosmicOrange)
                        Text("Current")
                            .font(BarklyFont.caption)
                            .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                    }
                    .accessibilityLabel("Current dog")
                }
            }
            .padding(.vertical, BarklySpacing.xs)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(isSelected ? [.isSelected] : [])
        .accessibilityValue(isSelected ? "Selected" : "Not selected")
    }
}

#Preview("Dog selector") {
    DogSelectorView()
        .environment(AppContainer())
}