//
//  ContentView.swift
//  DaddyFix
//
//  Brian temporary integration shell (Kenji Xcode blocked).
//  Embeds Brian AR + VisionService analyze/mock buttons.
//

import SwiftUI

struct ContentView: View {
    @State private var app = AppState()

    var body: some View {
        ZStack {
            ARViewContainer(
                sessionManager: app.sessionManager,
                raycastManager: app.raycastManager,
                showMeshOverlay: app.showMeshOverlay,
                autoPlaceMockAnnotations: false
            )
            .ignoresSafeArea()

            VStack {
                HStack {
                    statusChip
                    Spacer()
                    Toggle(isOn: $app.showMeshOverlay) {
                        Text("LiDAR mesh")
                            .font(.caption.weight(.semibold))
                    }
                    .toggleStyle(.button)
                    .padding(8)
                    .background(.ultraThinMaterial, in: Capsule())
                }
                .padding()

                Spacer()

                VStack(spacing: 10) {
                    if let label = app.selectedPartLabel {
                        Text("Selected: \(label)")
                            .font(.headline)
                    }
                    if let item = app.analysis?.detectedItem {
                        Text(item)
                            .font(.subheadline.weight(.semibold))
                    }
                    Text(app.statusMessage)
                        .font(.footnote)
                        .multilineTextAlignment(.center)
                    if let err = app.lastError {
                        Text(err)
                            .font(.caption2)
                            .foregroundStyle(.orange)
                            .multilineTextAlignment(.center)
                    }

                    HStack(spacing: 10) {
                        Button("Analyze (API mock)") {
                            Task { await app.analyzeMockAndPlace() }
                        }
                        .buttonStyle(.borderedProminent)

                        Button("Local mock") {
                            app.apply(AnalysisResult.waterHeaterMock)
                        }
                        .buttonStyle(.bordered)

                        Button("Clear") {
                            app.clear()
                        }
                        .buttonStyle(.bordered)
                    }
                }
                .padding()
                .frame(maxWidth: .infinity)
                .background(.ultraThinMaterial)
            }
        }
        .onAppear {
            app.wireAnnotationSelection()
        }
    }

    private var statusChip: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
            VStack(alignment: .leading, spacing: 2) {
                Text(app.sessionManager.trackingStatus.rawValue)
                    .font(.caption.weight(.semibold))
                Text(app.sessionManager.isLiDARAvailable ? "LiDAR ready" : "No LiDAR — planes only")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text("phase: \(app.phase.rawValue)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial, in: Capsule())
    }

    private var statusColor: Color {
        switch app.sessionManager.trackingStatus {
        case .normal: return .green
        case .initializing, .relocalizing: return .yellow
        case .limited: return .orange
        case .notAvailable: return .red
        }
    }
}

#Preview {
    ContentView()
}
