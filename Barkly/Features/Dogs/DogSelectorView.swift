import SwiftUI
import UIKit

struct DogSelectorView: View {
    @Environment(AppContainer.self) private var app
    @Environment(\.dismiss) private var dismiss
    @State private var showAddDog = false

    var body: some View {
        NavigationStack {
            Group {
                if app.dogs.isEmpty {
                    EmptyStateView(
                        icon: "pawprint",
                        title: "No dogs yet",
                        message: "Add your first dog so BARKLY can keep each dog's signals separate.",
                        actionTitle: "Add Your Dog",
                        action: {
                            Haptics.light()
                            showAddDog = true
                        }
                    )
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .accessibilityIdentifier("dog_selector_empty")
                } else {
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
                    .accessibilityIdentifier("dog_selector")
                }
            }
            .navigationTitle("Switch Dog")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    HStack(spacing: BarklySpacing.sm) {
                        Button {
                            Haptics.light()
                            showAddDog = true
                        } label: {
                            Label("Add Dog", systemImage: "plus")
                        }
                        .accessibilityLabel("Add a dog")
                        Button("Done") {
                            dismiss()
                        }
                        .foregroundStyle(BarklyColor.cosmicOrangeDeep)
                    }
                }
            }
            .sheet(isPresented: $showAddDog) {
                AddDogView()
                    .presentationDetents([.large])
                    .presentationDragIndicator(.visible)
            }
        }
        .presentationDragIndicator(.visible)
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