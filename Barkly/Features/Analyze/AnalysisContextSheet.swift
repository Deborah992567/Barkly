import SwiftUI

/// Edits the optional context signals attached to the next analysis.
/// Every control is optional and defaults to "not sure".
struct AnalysisContextSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Binding var context: AnalysisContextInput
    @State private var presenceIndex: Int?
    @State private var activityIndex: Int?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Picker("Owner presence", selection: $presenceIndex) {
                        Text("Not sure").tag(Int?.none)
                        ForEach(Array(OwnerPresence.allCases.enumerated()), id: \.element) { index, value in
                            Text(value.displayName).tag(Int?.some(index))
                        }
                    }
                    Picker("Activity", selection: $activityIndex) {
                        Text("Not sure").tag(Int?.none)
                        ForEach(Array(ActivityState.allCases.enumerated()), id: \.element) { index, value in
                            Text(value.displayName).tag(Int?.some(index))
                        }
                    }
                } header: {
                    Text("What was happening?")
                } footer: {
                    Text("Optional — BARKLY never requires context to analyze.")
                }

                Section("Recent events") {
                    Toggle("Fed recently", isOn: optionalToggle(\.recentFeeding))
                    Toggle("Walked recently", isOn: optionalToggle(\.recentWalk))
                    Toggle("Played recently", isOn: optionalToggle(\.recentPlay))
                    Toggle("Strangers around", isOn: optionalToggle(\.presenceOfStrangers))
                    Toggle("Other animals around", isOn: optionalToggle(\.presenceOfOtherAnimals))
                    Toggle("Recent stressful event", isOn: optionalToggle(\.recentStressfulEvent))
                }
            }
            .navigationTitle("Context")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Clear") {
                        context = .empty
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        syncSelections()
                        dismiss()
                    }
                }
            }
        }
        .onAppear {
            presenceIndex = context.ownerPresence.map { OwnerPresence.allCases.firstIndex(of: $0) ?? 0 }
            activityIndex = context.activityState.map { ActivityState.allCases.firstIndex(of: $0) ?? 0 }
        }
    }

    private func optionalToggle(_ keyPath: WritableKeyPath<AnalysisContextInput, Bool?>) -> Binding<Bool> {
        Binding(
            get: { context[keyPath: keyPath] ?? false },
            set: { context[keyPath: keyPath] = $0 ? true : nil }
        )
    }

    private func syncSelections() {
        context.ownerPresence = presenceIndex.map { OwnerPresence.allCases[$0] }
        context.activityState = activityIndex.map { ActivityState.allCases[$0] }
    }
}