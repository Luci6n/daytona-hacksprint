//
//  RepairGuideView.swift
//  DaddyFix
//
//  Kenji — sheet shown after tapping an AR annotation. Lists numbered
//  repair steps with safety notes, and a "Buy replacement" hand-off to
//  the x402 payment flow.
//

import SwiftUI

struct RepairGuideView: View {
    let analysis: AnalysisResult
    let selectedLabel: String?
    var onBuyTapped: () -> Void

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            List {
                if let selectedLabel {
                    Section {
                        Text(selectedLabel)
                            .font(.title3.weight(.semibold))
                    }
                }

                Section("Repair Steps") {
                    ForEach(analysis.repairSteps) { step in
                        VStack(alignment: .leading, spacing: 6) {
                            Text("\(step.step). \(step.instruction)")
                                .font(.body)

                            if let safetyNote = step.safetyNote {
                                Label(safetyNote, systemImage: "exclamationmark.triangle.fill")
                                    .font(.footnote)
                                    .foregroundStyle(.orange)
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }

                if let part = analysis.buyableParts.first {
                    Section("Replacement Part") {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(part.name).font(.headline)
                            Text(part.estimatedPrice).foregroundStyle(.secondary)
                        }

                        Button("Buy replacement") {
                            onBuyTapped()
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(!part.x402Ready)
                    }
                }

                Section {
                    Label(
                        "If you're unsure at any step, call a licensed professional.",
                        systemImage: "phone.fill"
                    )
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                }
            }
            .navigationTitle(analysis.detectedItem)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
            }
        }
    }
}

#Preview {
    RepairGuideView(
        analysis: .waterHeaterMock,
        selectedLabel: "ELCB",
        onBuyTapped: {}
    )
}
